# from django.shortcuts import render
# from .models import Product

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout

from .models import Product, CartItem, Order, OrderItem, Notification, Withdrawal
from .forms import ReviewForm

def home(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    products = Product.objects.all()

    if query:
        products = products.filter(title__icontains=query)

    if category:
        products = products.filter(category__iexact=category)

    categories = Product.objects.values_list('category', flat=True).distinct()

    return render(request, 'home.html', {
        'products': products,
        'categories': categories
    })

#......

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('/')

    product = Product.objects.get(id=product_id)

    if product.stock <= 0:
        return redirect('/')

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('/')



#.....

def cart_view(request):
    if not request.user.is_authenticated:
        return redirect('/admin/login/')

    items = CartItem.objects.filter(user=request.user)

    total = sum(item.product.price * item.quantity for item in items)

    return render(request, 'cart.html', {
        'items': items,
        'total': total
    })

#....

def remove_from_cart(request, item_id):
    item = CartItem.objects.get(id=item_id)
    item.delete()
    return redirect('cart')

#......

def increase_qty(request, item_id):
    item = CartItem.objects.get(id=item_id)
    item.quantity += 1
    item.save()
    return redirect('cart')


def decrease_qty(request, item_id):
    item = CartItem.objects.get(id=item_id)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect('cart')

#......

@login_required
def checkout(request):

    if request.method != "POST":
        return redirect('cart')

    items = CartItem.objects.filter(user=request.user)

    if not items:
        return redirect('cart')

    total = 0
    order = Order.objects.create(user=request.user, total_price=0)

    for item in items:

        if item.product.stock < item.quantity:
            return redirect('cart')

        total += item.product.price * item.quantity

        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity
        )

        Notification.objects.create(
            user=item.product.seller,
            message=f"Your product '{item.product.title}' was sold!"
        )

        item.product.stock -= item.quantity
        item.product.save()

    order.total_price = total
    order.save()

    items.delete()

    return render(request, "success.html", {"order": order})
#.....

def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "orders.html", {"orders": orders})

#....

def product_detail(request, id):
    product = Product.objects.get(id=id)
    return render(request, "product.html", {"product": product})

#.......

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

# def register(request):
#     form = UserCreationForm()

#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect("/")  # go home after success

#     return render(request, "home.html", {"register_form": form})

#.....

def logout_user(request):
    logout(request)
    return redirect('/')

#......

@login_required
def payment_page(request):

    if request.method == "POST":
        return checkout(request)

    return render(request, "payment.html")

#.....

@login_required
def seller_products(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, "seller_products.html", {"products": products})

#....

from .forms import ProductForm

@login_required
def sell_product(request):

    form = ProductForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        return redirect('/')

    return render(request, "sell.html", {"form": form})

#.....

@login_required
def seller_dashboard(request):

    products = Product.objects.filter(seller=request.user)
    orders = OrderItem.objects.filter(product__seller=request.user)

    total_sales = sum(item.quantity for item in orders)
    total_earnings = sum(item.product.price * item.quantity for item in orders)

    chart_labels = []
    chart_data = []

    for product in products:
        product_orders = orders.filter(product=product)
        earnings = sum(o.product.price * o.quantity for o in product_orders)

        chart_labels.append(product.title)
        chart_data.append(float(earnings))

    return render(request, "seller_dashboard.html", {
        "products": products,
        "total_sales": total_sales,
        "total_earnings": total_earnings,
        "orders": orders,
        "labels": chart_labels,
        "data": chart_data
    })

#......

import json
from django.shortcuts import render


def dashboard(request):

    labels = ["Jan", "Feb", "Mar", "Apr"]
    data = [120, 90, 150, 200]

    context = {
        "labels": json.dumps(labels),
        "data": json.dumps(data),
    }

    return render(request, "home.html", context)

#....

@login_required
def add_review(request, product_id):

    product = Product.objects.get(id=product_id)
    form = ReviewForm(request.POST or None)

    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        return redirect("product_detail", id=product_id)

    return render(request, "add_review.html", {"form": form})

#.....

@login_required
def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "notifications.html", {"notes": notes})

#......

@login_required
def withdraw(request):

    orders = OrderItem.objects.filter(product__seller=request.user)

    total_earnings = sum(o.product.price * o.quantity for o in orders)

    withdrawn = sum(w.amount for w in Withdrawal.objects.filter(seller=request.user))

    available = total_earnings - withdrawn

    if request.method == "POST":

        Withdrawal.objects.create(
            seller=request.user,
            amount=available
        )

        return redirect("seller_dashboard")

    return render(request, "withdraw.html", {"available": available})

from django.http import JsonResponse
from django.contrib.auth import authenticate, login

def popup_login(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )

        if user:
            login(request,user)

            if not request.POST.get("remember"):
                request.session.set_expiry(0)

            return JsonResponse({"success":True})
        else:
            return JsonResponse({"success":False,"error":"Invalid login"})

    return JsonResponse({"success":False})

def register(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)   # auto login
            return redirect("/")

    return render(request, "home.html", {"register_form": form})

#........

def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")

def support(request):
    return render(request, "support.html")

def careers(request):
    return render(request, "careers.html")

def home(request):
    profile = None
    if request.user.is_authenticated:
        profile = request.user.profile

    return render(request,"home.html",{
        "profile":profile
    })

from .forms import ProfileImageForm
from django.contrib.auth.decorators import login_required

@login_required
def upload_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileImageForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("/")
    else:
        form = ProfileImageForm(instance=profile)

    return render(request,"upload_profile.html",{"form":form})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Product, Profile

@login_required
def profile_page(request):
    profile = request.user.profile
    products = Product.objects.filter(seller=request.user)

    context = {
        "profile": profile,
        "products": products
    }
    return render(request,"profile.html",context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def edit_profile(request):
    return render(request, "edit_profile.html")

@login_required
def upgrade_account(request):
    return render(request, "upgrade.html")

@login_required
def verify_account(request):
    return render(request, "verify.html")

@login_required
def sponsor_listing(request):
    return render(request, "sponsor.html")
# Create your views here.
