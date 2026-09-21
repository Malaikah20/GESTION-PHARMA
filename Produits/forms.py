from django import forms
from .models import Client, Fournisseur, Produit, Vente, LigneVente
from django.forms import BaseInlineFormSet, inlineformset_factory
class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = [
            'nom', 'categorie', 'fournisseur', 'prix_de_vente', 
            'prix_achat', 'stock', 'seuil_alerte', 'numero_de_lot', 
            'date_de_peremption', 'image', 'description', 'actif'
        ]
        widgets = {
            'date_de_peremption': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'placeholder': 'Pour votre sante -----------'}),
            'actif': forms.CheckboxInput(),
        }

class clientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'prenom', 'adresse_mail', 'telephone', 'adresse'
                  , 'note', 
                  ]
        widgets = {
            'adresse': forms.Textarea(attrs={
                'placeholder': 'Adresse du client'}),
            'note': forms.Textarea(attrs={
                'placeholder': 'Notes sur le pharmacien'}),
        }

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'adresse_mail', 'contact', 'telephone', 'adresse', 'note', 'actif']
        widgets = {
            'adresse': forms.Textarea(attrs={'placeholder': 'Adresse du fournisseur'}),
            'note': forms.Textarea(attrs={'placeholder': 'Notes sur le fournisseur'}),
            'actif': forms.CheckboxInput(),
        }

class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        fields = ['client', 'mode_de_paiement', 'remise', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].empty_label = "client de passage"  # Valeur par défaut pour le champ client

class LigneVenteForm(forms.ModelForm):
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all(), 
        empty_label="Choisir un produit"

    )
    quantite = forms.IntegerField(min_value=1, required=False)
    prix_unitaire = forms.DecimalField(required=False, disabled=True)

    class Meta:
        model = LigneVente
        fields = ['produit', 'quantite', 'prix_unitaire']

    def clean (self):
        cleaned_data = super().clean()
        produit = cleaned_data.get('produit')
        quantite = cleaned_data.get('quantite')

        if produit and not quantite:
            raise forms.ValidationError("Veuillez saisir la quantité pour le produit sélectionné.")
        if quantite and not produit:
            raise forms.ValidationError("Veuillez sélectionner un produit pour la quantité saisie.")
        if produit and quantite and quantite > produit.stock:
            raise forms.ValidationError(
                f"stock insuffisant pour le produit {produit.nom}. Stock disponible: {produit.stock}, Quantité demandée: {quantite}."
            )
        return cleaned_data

class BaseLigneVenteFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        lignes = [
            form.cleaned_data for form in self.forms
            if form.cleaned_data and form.cleaned_data.get('produit')
        ]
        if not lignes:
            raise forms.ValidationError("Ajoutez au moins un produit à la vente.")
        produits = [ligne['produit'].pk for ligne in lignes]
        if len(produits) != len(set(produits)):
            raise forms.ValidationError("Un produit ne peut apparaître qu'une seule fois dans une vente.")
lignevente_formset = inlineformset_factory(
    Vente, LigneVente, 
    form=LigneVenteForm, 
    formset=BaseLigneVenteFormSet,
    extra=5, 
    can_delete=False

    )





















