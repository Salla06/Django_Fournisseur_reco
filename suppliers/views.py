from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Avg, Count, Sum, Q
from functools import wraps
import json

from recommendations.models import CustomUser, Product, Category, Rating, Comment, Purchase
from .models import Supplier, SupplierProduct
from .forms import SupplierRegisterForm, SupplierLoginForm, SupplierProfileForm, ProductForm


# ── Décorateur fournisseur ────────────────────────────────────────────────────

def supplier_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('supplier_login')
        try:
            _ = request.user.supplier
        except Supplier.DoesNotExist:
            messages.error(request, 'Accès réservé aux fournisseurs.')
            return redirect('supplier_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── AUTH ─────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated and hasattr(request.user, 'supplier'):
        return redirect('supplier_dashboard')

    form = SupplierRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        company_name = form.cleaned_data['company_name']
        password = form.cleaned_data['password1']

        # username dérivé de l'email
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = CustomUser(
            email=email,
            username=username,
            is_active=False,
        )
        user.set_password(password)
        user.save()

        # Envoyer l'email d'activation
        _send_activation_email(request, user, company_name)

        request.session['pending_company_name'] = company_name
        return redirect('supplier_email_sent')

    return render(request, 'suppliers/register.html', {'form': form})


def _send_activation_email(request, user, company_name):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    activation_url = f"{protocol}://{domain}/suppliers/activate/{uid}/{token}/"

    subject = 'Activez votre compte fournisseur RecoShop'
    html_message = render_to_string('suppliers/emails/activation.html', {
        'user': user,
        'company_name': company_name,
        'activation_url': activation_url,
    })
    plain_message = (
        f"Bonjour,\n\n"
        f"Pour activer votre compte fournisseur ({company_name}) sur RecoShop, "
        f"cliquez sur ce lien :\n{activation_url}\n\n"
        f"Ce lien expire dans 24 heures.\n\nL'équipe RecoShop"
    )

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@recoshop.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        # En dev sans serveur email, on continue quand même
        pass


def email_sent_view(request):
    return render(request, 'suppliers/email_sent.html')


def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        # Récupérer le nom d'entreprise depuis la session ou utiliser un défaut
        company_name = request.session.pop('pending_company_name', user.username)

        Supplier.objects.get_or_create(
            user=user,
            defaults={'company_name': company_name},
        )

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.success(request, f'Bienvenue sur l\'espace fournisseur, {company_name} !')
        return redirect('supplier_dashboard')
    else:
        messages.error(request, 'Le lien d\'activation est invalide ou a expiré.')
        return redirect('supplier_register')


def login_view(request):
    if request.user.is_authenticated and hasattr(request.user, 'supplier'):
        return redirect('supplier_dashboard')

    form = SupplierLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip()
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, 'Email ou mot de passe incorrect.')
        elif not hasattr(user, 'supplier'):
            messages.error(
                request,
                'Ce compte n\'est pas un compte fournisseur. '
                'Utilisez l\'espace client pour vous connecter.'
            )
        else:
            login(request, user)
            return redirect('supplier_dashboard')

    return render(request, 'suppliers/login.html', {'form': form})


@supplier_required
def logout_view(request):
    logout(request)
    return redirect('supplier_login')


# ── DASHBOARD ────────────────────────────────────────────────────────────────

@supplier_required
def dashboard_view(request):
    supplier = request.user.supplier
    product_ids = supplier.supplier_products.values_list('product_id', flat=True)
    products = Product.objects.filter(id__in=product_ids).select_related('category')

    # Statistiques globales
    total_products = products.count()

    stats = products.aggregate(
        avg_price=Avg('price'),
        avg_rating=Avg('ratings__score'),
    )
    avg_price = round(stats['avg_price'] or 0, 0)
    avg_rating = round(stats['avg_rating'] or 0, 1)

    # Produit le mieux noté
    best_rated = (
        products.annotate(avg_r=Avg('ratings__score'))
        .order_by('-avg_r')
        .first()
    )

    # Produit le plus vendu
    best_sold = (
        products.annotate(total_sold=Sum('purchase__quantity'))
        .order_by('-total_sold')
        .first()
    )

    # Données pour le graphique (notes moyennes par produit, top 10)
    chart_products = (
        products.annotate(avg_r=Avg('ratings__score'), rc=Count('ratings'))
        .filter(rc__gt=0)
        .order_by('-avg_r')[:10]
    )
    chart_labels = [p.name[:20] for p in chart_products]
    chart_data = [float(p.avg_r or 0) for p in chart_products]

    # 5 derniers commentaires
    recent_comments = (
        Comment.objects.filter(product__in=products)
        .select_related('user', 'product')
        .order_by('-created_at')[:5]
    )

    context = {
        'supplier': supplier,
        'total_products': total_products,
        'avg_price': avg_price,
        'avg_rating': avg_rating,
        'best_rated': best_rated,
        'best_sold': best_sold,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'recent_comments': recent_comments,
        'active': 'dashboard',
    }
    return render(request, 'suppliers/dashboard.html', context)


# ── PRODUITS ─────────────────────────────────────────────────────────────────

@supplier_required
def products_view(request):
    supplier = request.user.supplier
    product_ids = supplier.supplier_products.values_list('product_id', flat=True)

    search_q = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')

    products = (
        Product.objects.filter(id__in=product_ids)
        .select_related('category')
        .annotate(avg_r=Avg('ratings__score'), rating_count=Count('ratings'))
    )

    if search_q:
        products = products.filter(
            Q(name__icontains=search_q) | Q(brand__icontains=search_q)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)

    products = products.order_by('-id')

    categories = Category.objects.filter(
        products__id__in=product_ids
    ).distinct()

    context = {
        'products': products,
        'categories': categories,
        'search_q': search_q,
        'current_category': category_slug,
        'active': 'products',
    }
    return render(request, 'suppliers/products.html', context)


@supplier_required
def product_add_view(request):
    supplier = request.user.supplier
    form = ProductForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        product = form.save()
        SupplierProduct.objects.create(supplier=supplier, product=product)
        messages.success(request, f'Produit « {product.name} » créé avec succès !')
        return redirect('supplier_products')

    categories = Category.objects.all().order_by('name')
    context = {
        'form': form,
        'categories': categories,
        'action': 'add',
        'active': 'products',
    }
    return render(request, 'suppliers/product_form.html', context)


@supplier_required
def product_edit_view(request, pk):
    supplier = request.user.supplier
    supplier_product = get_object_or_404(
        SupplierProduct, supplier=supplier, product_id=pk
    )
    product = supplier_product.product

    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Produit « {product.name} » mis à jour !')
        return redirect('supplier_products')

    categories = Category.objects.all().order_by('name')
    context = {
        'form': form,
        'product': product,
        'categories': categories,
        'action': 'edit',
        'active': 'products',
    }
    return render(request, 'suppliers/product_form.html', context)


@supplier_required
def product_delete_view(request, pk):
    supplier = request.user.supplier
    supplier_product = get_object_or_404(
        SupplierProduct, supplier=supplier, product_id=pk
    )
    product = supplier_product.product

    if request.method == 'GET':
        return render(request, 'suppliers/product_delete.html', {
            'product': product,
            'active': 'products',
        })
    return redirect('supplier_products')


@supplier_required
@require_POST
def product_delete_confirm_view(request, pk):
    supplier = request.user.supplier
    supplier_product = get_object_or_404(
        SupplierProduct, supplier=supplier, product_id=pk
    )
    product = supplier_product.product
    product_name = product.name
    supplier_product.delete()
    product.delete()
    messages.success(request, f'Produit « {product_name} » supprimé.')
    return redirect('supplier_products')


@supplier_required
def product_detail_view(request, pk):
    supplier = request.user.supplier
    supplier_product = get_object_or_404(
        SupplierProduct, supplier=supplier, product_id=pk
    )
    product = supplier_product.product

    # Notes
    ratings = Rating.objects.filter(product=product)
    avg_rating = ratings.aggregate(avg=Avg('score'))['avg'] or 0
    rating_dist = {i: 0 for i in range(1, 6)}
    for r in ratings:
        rating_dist[r.score] += 1

    # Commentaires
    comments = Comment.objects.filter(product=product).select_related('user').order_by('-created_at')

    # Ventes
    purchases = Purchase.objects.filter(product=product).order_by('-purchased_at')
    total_sold = purchases.aggregate(total=Sum('quantity'))['total'] or 0

    # Évolution des ventes par mois (6 derniers mois)
    from django.utils import timezone
    from datetime import timedelta
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_sales = (
        purchases.filter(purchased_at__gte=six_months_ago)
        .extra(select={'month': "strftime('%%Y-%%m', purchased_at)"})
        .values('month')
        .annotate(total=Sum('quantity'))
        .order_by('month')
    )
    sales_labels = json.dumps([s['month'] for s in monthly_sales])
    sales_data = json.dumps([s['total'] for s in monthly_sales])

    # Dist ratings pour graphique
    dist_labels = json.dumps(['1★', '2★', '3★', '4★', '5★'])
    dist_data = json.dumps([rating_dist[i] for i in range(1, 6)])

    context = {
        'product': product,
        'avg_rating': round(avg_rating, 1),
        'rating_count': ratings.count(),
        'rating_dist': rating_dist,
        'dist_labels': dist_labels,
        'dist_data': dist_data,
        'comments': comments,
        'total_sold': total_sold,
        'sales_labels': sales_labels,
        'sales_data': sales_data,
        'active': 'products',
    }
    return render(request, 'suppliers/product_detail.html', context)


# ── PROFIL ────────────────────────────────────────────────────────────────────

@supplier_required
def profile_view(request):
    supplier = request.user.supplier
    form = SupplierProfileForm(request.POST or None, request.FILES or None, instance=supplier)

    if request.method == 'POST':
        if form.is_valid():
            form.save()

            # Changement de mot de passe
            p1 = request.POST.get('new_password1', '')
            p2 = request.POST.get('new_password2', '')
            if p1 and p1 == p2:
                request.user.set_password(p1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Mot de passe mis à jour.')
            elif p1 and p1 != p2:
                messages.error(request, 'Les mots de passe ne correspondent pas.')

            messages.success(request, 'Profil mis à jour !')
            return redirect('supplier_profile')

    context = {
        'supplier': supplier,
        'form': form,
        'active': 'profile',
    }
    return render(request, 'suppliers/profile.html', context)
