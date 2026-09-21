from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom']
    search_fields = ['nom']

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'contact', 'telephone', 'adresse_mail', 'actif']
    list_filter = ['actif']  
    search_fields = ['nom', 'contact', 'adresse_mail'] 

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'telephone', 'adresse_mail', 'actif']
    search_fields = ['nom', 'prenom', 'adresse_mail', 'telephone']

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'categorie', 'fournisseur', 'prix_de_vente', 'prix_achat', 'stock', 'seuil_alerte', 'actif']
    list_filter = ['actif', 'categorie', 'fournisseur']
    search_fields = ['nom', 'numero_de_lot']

class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 0
    
@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['numero_facture', 'client', 'date', 'mode_de_paiement', 'total']  
    list_filter = ['statut', 'mode_de_paiement']
    inlines = [LigneVenteInline]

        