from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from .models import Produit, Fournisseur, Client, Vente
from .forms import ProduitForm, clientForm, FournisseurForm, VenteForm, lignevente_formset
from django.db.models import Sum, Count, Max

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def produits_liste(request):
    produits = Produit.objects.select_related('categorie').annotate(   # Utilisation de select_related pour optimiser la requête
        total_ventes=Sum('lignes_vente__quantite')
    )  
    return render(request, 'produits/liste.html', {'produits': produits}) 


@login_required
def produits_form(request, pk=None):
    produit= get_object_or_404(Produit, pk=pk) if pk else None

    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit enregistré avec succès")   
            return redirect('produits_liste') 

    else:
        form = ProduitForm(instance=produit)
    return render(request, 'produits/form.html', {'form': form, 'produit': produit})

@require_POST            
def produits_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    produit.delete()
    messages.success(request, "Produit supprimé avec succès")
    return redirect('produits_liste')
    # return render(request, 'produits/delete.html', {'produit': produit})  

@login_required
def stock_liste(request):
    produits = Produit.objects.all()  # Récupère tous les produits de la base de données
    return render(request, 'stock/liste.html', {'produits': produits})

@login_required
def ventes_liste(request):
    vente = Vente.objects.select_related('client').prefetch_related('lignes')
    return render(request, 'ventes/liste.html', {'ventes': vente})

@login_required
def ventes_form(request):
    vente_form = VenteForm(request.POST or None)
    formset = lignevente_formset(request.POST or None)

    if request.method == 'POST' and vente_form.is_valid() and formset.is_valid():
        with transaction.atomic():
            vente = vente_form.save(commit=False)
            vente.statut = Vente.Statut.TERMINEE
            lignes = [
                form.cleaned_data for form in formset
                if form.cleaned_data and form.cleaned_data.get('produit')
            ]
            produits = {
                produit.pk: Produit.objects.select_for_update().get(pk=produit.pk)
                for produit in (ligne['produit'] for ligne in lignes)
            }
            sous_total = 0
            for ligne in lignes:
                produit = produits[ligne['produit'].pk]
                quantite = ligne['quantite']
                if quantite > produit.stock:
                    formset._non_form_errors = formset.error_class(
                        [f"Stock insuffisant pour {produit.nom} : {produit.stock} disponible(s)."]
                    )
                    break
                sous_total += quantite * produit.prix_de_vente
            else:
                if vente.remise > sous_total:
                    vente_form.add_error('remise', "La remise ne peut pas dépasser le sous-total.")
                else:
                    vente.total = sous_total - vente.remise
                    vente.save()
                    for ligne in lignes:
                        produit = produits[ligne['produit'].pk]
                        produit.stock -= ligne['quantite']
                        produit.quantite = produit.stock
                        produit.save(update_fields=['stock', 'quantite'])
                        ligne_form = next(
                            form for form in formset
                            if form.cleaned_data.get('produit').pk == produit.pk
                        )
                        ligne_form.instance.vente = vente
                        ligne_form.instance.prix_unitaire = produit.prix_de_vente
                        ligne_form.instance.quantite = ligne['quantite']
                        ligne_form.instance.produit = produit
                        ligne_form.instance.save()
                    messages.success(request, f"Vente {vente.numero_facture} enregistrée.")
                    return redirect('factures_detail', pk=vente.pk)

    produits_catalogue = Produit.objects.filter(actif=True).order_by('nom')
    return render(request, 'ventes/form.html', {
        'vente_form': vente_form,
        'formset': formset,
        'produits_catalogue': produits_catalogue,
    })

@login_required
def clients_liste(request):
    clients = Client.objects.annotate(
        nb_achats=Count('ventes'),  # Calcule le nombre total d'achats pour chaque client
        dernierre_achat=Max('ventes__date'),  # Calcule la date du dernier achat pour chaque client 
    )
    return render(request, 'clients/liste.html', {'clients': clients})

@login_required
def clients_form(request, pk=None):
    client = get_object_or_404(Client, pk=pk) if pk else None

    if request.method == 'POST':
        form = clientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client enregistré avec succès")
            return redirect('clients_liste')
    else:
        form = clientForm(instance=Client())
    return render(request, 'clients/form.html', {'form': form, 'client': client})

@login_required
@require_POST
def clients_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.delete()
    messages.success(request, "Client supprimé avec succès")
    return redirect('clients_liste')
@login_required
def fournisseurs_liste(request):
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'fournisseurs/liste.html', {'fournisseurs': fournisseurs})

@login_required
def fournisseurs_form(request, pk=None):
    fournisseurs = get_object_or_404(Fournisseur, pk=pk) if pk else None
    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseurs)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur enregistré avec succès")
            return redirect('fournisseurs_liste')
    else:
        form = FournisseurForm(instance=Fournisseur())
    return render(request, 'fournisseurs/form.html', {'form': form, 'fournisseur': fournisseurs})

@login_required
@require_POST
def fournisseurs_delete(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    fournisseur.delete()
    messages.success(request, "Fournisseur supprimé avec succès")
    return redirect('fournisseurs_liste')

@login_required
def factures_liste(request):
    ventes = Vente.objects.select_related('client').prefetch_related('lignes')  # Optimisation des requêtes pour éviter les requêtes supplémentaires
    return render(request, 'factures/liste.html', {'ventes': ventes})


def factures_detail(request, pk):
    ventes_form = get_object_or_404(
        Vente.objects.select_related('client').prefetch_related('lignes__produit'),
        pk=pk,
        )
    return render(request, 'factures/detail.html', {'vente': ventes_form})


@login_required
def statistiques(request):
    maintenant = timezone.now()
    debut_30_jours = maintenant - timedelta(days=30)
    ventes_terminees = Vente.objects.filter(
        statut=Vente.Statut.TERMINEE,
        date__gte=debut_30_jours,
        date__lte=maintenant,
    )
    chiffre_affaires = ventes_terminees.aggregate(total=Sum('total'))['total'] or 0
    nombre_ventes = ventes_terminees.count()
    panier_moyen = chiffre_affaires / nombre_ventes if nombre_ventes else 0

    produits_en_alerte = Produit.objects.filter(
        actif=True,
        stock__lte=F('seuil_alerte'),
    ).count()
    ventes_par_jour = ventes_terminees.filter(
        date__gte=maintenant - timedelta(days=6)
    ).annotate(jour=TruncDate('date')).values('jour').annotate(
        total=Sum('total')
    ).order_by('jour')
    totaux_par_jour = {element['jour']: element['total'] or 0 for element in ventes_par_jour}
    noms_jours = ('Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim')
    jours = []
    for decalage in range(6, -1, -1):
        jour = (maintenant - timedelta(days=decalage)).date()
        jours.append({
            'label': noms_jours[jour.weekday()],
            'date': jour,
            'total': totaux_par_jour.get(jour, 0),
        })
    maximum_journalier = max((jour['total'] for jour in jours), default=0)
    for jour in jours:
        jour['hauteur'] = (jour['total'] / maximum_journalier * 100) if maximum_journalier else 0

    produits_populaires = Produit.objects.filter(
        lignes_vente__vente__statut=Vente.Statut.TERMINEE,
        lignes_vente__vente__date__gte=debut_30_jours,
    ).annotate(
        quantite_vendue=Sum('lignes_vente__quantite')
    ).order_by('-quantite_vendue', 'nom')[:5]

    return render(request, 'statistiques/index.html', {
        'chiffre_affaires': chiffre_affaires,
        'nombre_ventes': nombre_ventes,
        'panier_moyen': panier_moyen,
        'produits_en_alerte': produits_en_alerte,
        'jours': jours,
        'produits_populaires': produits_populaires,
    })


@login_required
def notifications(request):
    maintenant = timezone.now()
    aujourd_hui = timezone.localdate()
    notifications_liste = []
    produits = Produit.objects.filter(actif=True).order_by('nom')

    for produit in produits:
        if produit.stock == 0:
            notifications_liste.append({
                'type': 'danger',
                'titre': f'Rupture de stock : {produit.nom}',
                'detail': 'Aucune unite disponible.',
            })
        elif produit.stock <= produit.seuil_alerte:
            notifications_liste.append({
                'type': 'warning',
                'titre': f'Stock faible : {produit.nom}',
                'detail': f'{produit.stock} unite(s) restante(s) (seuil : {produit.seuil_alerte}).',
            })

        if produit.date_de_peremption:
            jours_avant_peremption = (produit.date_de_peremption - aujourd_hui).days
            if jours_avant_peremption < 0:
                notifications_liste.append({
                    'type': 'danger',
                    'titre': f'Produit expire : {produit.nom}',
                    'detail': f'Perime depuis le {produit.date_de_peremption.strftime("%d/%m/%Y")}.',
                })
            elif jours_avant_peremption <= 30:
                notifications_liste.append({
                    'type': 'danger',
                    'titre': f'Peremption proche : {produit.nom}',
                    'detail': f'Peremption le {produit.date_de_peremption.strftime("%d/%m/%Y")} ({jours_avant_peremption} jour(s)).',
                })

    ventes_recentes = Vente.objects.filter(
        statut=Vente.Statut.TERMINEE,
        date__gte=maintenant - timedelta(hours=24),
    ).select_related('client').order_by('-date')[:5]
    for vente in ventes_recentes:
        client = str(vente.client) if vente.client else 'Client de passage'
        notifications_liste.append({
            'type': 'info',
            'titre': f'Vente {vente.numero_facture} enregistree',
            'detail': f'{client} - {vente.total:.2f} € - {vente.date.strftime("%d/%m/%Y %H:%M")}.',
        })

    return render(request, 'notifications/liste.html', {
        'notifications': notifications_liste,
    })


def parametres(request):
    return render(request, 'parametres/index.html')


def login(request):
    return render(request, 'auth/login.html')

def login (request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirige vers la page d'accueil si l'utilisateur est déjà connecté

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')  # Redirige vers la page d'accueil après la connexion réussie
            
        messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    return render(request, 'auth/login.html')

def logout_view(request):
    auth_logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')  # Redirige vers la page de connexion après la déconnexion

def produits_edit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    # Votre logique de modification ici...
    return render(request, 'Produits/form.html', {'produit': produit})
