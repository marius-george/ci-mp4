from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from django.core.exceptions import ObjectDoesNotExist
import stripe
from django.conf import settings
from django.contrib.auth.models import Group, User
from .forms import SignUpForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm


def home(request, category_slug=None):
    category_page = None
    products = None
    if category_slug:
        category_page = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category_page, available=True)
    else:
        products = Product.objects.filter(available=True)
    return render(request, 'home.html', {'category': category_page, 'products': products})

def productPage(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)

    except Exception as e:
        raise e
    return render(request, 'product.html', {'product': product})


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart.save()
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart
        )
        cart_item.save()

    return redirect('cart_detail')


def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
    except ObjectDoesNotExist:
        pass
    else:
        for item in cart_items:
            total += (item.product.price * item.quantity)
            counter += item.quantity

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'E - Shop - New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY

    if request.method == 'POST':
        try:
            post = request.POST
            token = post['stripeToken']
            email = post['stripeEmail']
            billingName = post['stripeBillingName']
            billingAddress1 = post['stripeBillingAddressLine1']
            billingCity = post['stripeBillingAddressCity']
            billingPostcode = post['stripeBillingAddressZip']
            billingCountry = post['stripeBillingAddressCountryCode']
            shippingName = post['stripeShippingName']
            shippingAddress1 = post['stripeShippingAddressLine1']
            shippingCity = post['stripeShippingAddressCity']
            shippingPostcode = post['stripeShippingAddressZip']
            shippingCountry = post['stripeShippingAddressCountryCode']

            customer = stripe.Customer.create(email=email, source=token)
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency='usd',
                description=description,
                customer=customer.id
            )

            try:
                order_details = Order.objects.create(
                    token=token,
                    total=total,
                    emailAddress=email,
                    billingName=billingName,
                    billingAddress1=billingAddress1,
                    billingCity=billingCity,
                    billingPostcode=billingPostcode,
                    billingCountry=billingCountry,
                    shippingName=shippingName,
                    shippingAddress1=shippingAddress1,
                    shippingCity=shippingCity,
                    shippingPostcode=shippingPostcode,
                    shippingCountry=shippingCountry
                )
                order_details.save()

                for ci in cart_items:
                    oi = OrderItem.objects.create(
                        product=ci.product.name,
                        quantity=ci.quantity,
                        price=ci.product.price,
                        order=order_details
                    )
                    oi.save()

                    product = Product.objects.get(id=ci.product.id)
                    product.stock = int(ci.product.stock - ci.quantity)
                    product.save()
                    ci.delete()

                    print('the order has been created')

                return redirect('thankyou_page', order_details.id)
            except ObjectDoesNotExist:
                pass

        except stripe.error.CardError as e:
            return False, e

    return render(
        request,
        'cart.html',
        dict(
            cart_items=cart_items,
            total=total,
            counter=counter,
            data_key=data_key,
            stripe_total=stripe_total,
            description=description
        )
    )


def cart_remove(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')

def cart_remove_product(request, product_id):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        product = get_object_or_404(Product, id=product_id)
        cart_item = CartItem.objects.get(product=product, cart=cart)
    except Cart.DoesNotExist:
        # Handle the case where the cart does not exist
        raise Http404("Cart not found.")
    except CartItem.DoesNotExist:
        # Handle the case where the cart item does not exist
        raise Http404("Item not found in the cart.")
    else:
        # If all objects are properly retrieved, delete the cart item
        cart_item.delete()
    
    # Redirect to the cart detail page after the item is removed
    return redirect('cart_detail')
    

def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
            login(request, signup_user)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def signinView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')


def thankyou_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'customer_order': customer_order})