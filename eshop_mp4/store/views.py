from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from .models import Category, Product, Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist

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
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter))


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
    
# def cart_remove_product(request, product_id):
#     cart = Cart.objects.get(cart_id=_cart_id(request))
#     product = get_object_or_404(Product, id=product_id)
#     cart_item = CartItem.objects.get(product=product, cart=cart)
#     cart_item.delete()
#     return redirect('cart_detail')
    


# def _cart_id(request):
#     cart = request.session.session_key
#     if not cart:
#         cart = request.session.create()
#     return cart

# def add_cart(request, product_id):
#     product = Product.objects.get(id=product_id)
#     try:
#         cart = Cart.objects.get(cart_id=_cart_id(request))
#     except Cart.DoesNotExist:
#         cart = Cart.objects.create(
#             cart_id = _cart_id(request)
#             )
#         cart.save()
#     try:
#         cart_item = CartItem.objects.get(product=product, cart=cart)
#         cart_item.quantity += 1
#         cart_item.save()
#     except CartItem.DoesNotExist:
#         cart_item = CartItem.objects.create(
#             product = product,
#             quantity = 1,
#             cart = cart
#         )
#     cart_item.save()

#     return redirect('cart_detail')


# def cart_detail(request, total=0, counter=0, cart_items=None):
#     try:
#         cart_id = request.session.get("cart_id", None)  # Make sure to retrieve the cart_id safely from the session
#         if cart_id:
#             cart = Cart.objects.get(cart_id=cart_id)
#             cart_items = CartItem.objects.filter(cart=cart, active=True)
#             for cart_item in cart_items:
#                 total += (cart_item.product.price * cart_item.quantity)
#                 counter += cart_item.quantity
#         else:
#             cart_items = []  # If no cart_id or cart is found, use an empty list for cart_items
#     except ObjectDoesNotExist:
#         cart_items = []  # Handle the case when the cart does not exist

#     context = {
#         'cart_items': cart_items,
#         'total': total,
#         'counter': counter
#     }
#     return render(request, 'cart.html', context)



# def add_cart(request, product_id):
#     # Get the product or return 404 if not found
#     product = get_object_or_404(Product, id=product_id)

#     # Get or create a cart
#     cart_id = _cart_id(request)
#     cart, created = Cart.objects.get_or_create(cart_id=cart_id)

#     # Check if the product already exists in the cart
#     cart_item, item_created = CartItem.objects.get_or_create(product=product, cart=cart)

#     # If the item already exists and there's available stock, increment quantity
#     if not item_created and cart_item.quantity < product.stock:
#         cart_item.quantity += 1
#         cart_item.save()

#     # If the item doesn't exist, add it to the cart
#     elif item_created:
#         cart_item.quantity = 1
#         cart_item.save()

#     return redirect('cart_detail')