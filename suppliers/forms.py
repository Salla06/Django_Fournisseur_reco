from django import forms
from recommendations.models import CustomUser, Product, Category
from .models import Supplier


class SupplierRegisterForm(forms.Form):
    email = forms.EmailField(label='Adresse email')
    company_name = forms.CharField(max_length=200, label='Nom de l\'entreprise')
    password1 = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmer le mot de passe')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Cet email est déjà utilisé.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Les mots de passe ne correspondent pas.')
        return cleaned


class SupplierLoginForm(forms.Form):
    email = forms.EmailField(label='Adresse email')
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')


class SupplierProfileForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ('company_name', 'phone', 'address', 'bio', 'logo')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'name', 'category', 'description', 'price', 'original_price',
            'image_url', 'image_color', 'image_emoji', 'tags', 'brand',
            'stock', 'is_featured',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'image_color': forms.TextInput(attrs={'type': 'color'}),
            'tags': forms.TextInput(attrs={'placeholder': 'ex: sport, running, extérieur'}),
        }
        labels = {
            'name': 'Nom du produit',
            'category': 'Catégorie',
            'description': 'Description',
            'price': 'Prix (FCFA)',
            'original_price': 'Prix original (FCFA) — optionnel',
            'image_url': 'URL de l\'image',
            'image_color': 'Couleur de la carte',
            'image_emoji': 'Emoji représentatif',
            'tags': 'Tags (séparés par des virgules)',
            'brand': 'Marque',
            'stock': 'Stock disponible',
            'is_featured': 'Produit mis en avant',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['original_price'].required = False
        self.fields['image_url'].required = False
        self.fields['brand'].required = False
        self.fields['tags'].required = False
