from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from store.models import Variation
from .models import Cart,CartItem
from store.models import Product
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

# Create your views here.

def _CartId(request): #_FunctionName -> private function
    cart = request.session.session_key #session id
    if not cart:
        cart = request.session.create() #if there is no session,this method will create one
    return cart
def AddToCart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                #color = request.POST['color'] #name of the select box in 'product_detail.html'
                #print(key,value)
                try:
                    variation = Variation.objects.get(product=product,variation_category__iexact=key,variation_value__iexact=value) #__iexact will ignore case sensitiveness.
                    #product=product -> this is for specifying the product which the particular variation belongs to. 'product' is the field name in variation model and it is assigned to the 'product' variable here in this view.
                    product_variation.append(variation)#to store these values in CartItem
                except:
                    pass

        is_cart_item_exists = CartItem.objects.filter(product=product,user=current_user).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product,user=current_user)
            existing_variations_list=[]
            id=[]
            for item in cart_item:
                existing_variation=item.variations.all()
                existing_variations_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in existing_variations_list:
                #increase_cart_item_id
                index = existing_variations_list.index(product_variation)
                item_id=id[index]
                item=CartItem.objects.get(product=product,id=item_id)
                item.quantity += 1
                item.save()

            else:
                item = CartItem.objects.create(product=product,quantity=1,user=current_user,)
            #check if the product_variation list is empty or not, if it is empty then we are just going to update the quantity and if it is not empty we are going to add the item to the database
                if len(product_variation)>0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(product=product,quantity=1,user=current_user)
            if len(product_variation)>0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
    #if user is not authenticated
    else:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                #color = request.POST['color'] #name of the select box in 'product_detail.html'
                #print(key,value)
                try:
                    variation = Variation.objects.get(product=product,variation_category__iexact=key,variation_value__iexact=value) #__iexact will ignore case sensitiveness.
                    #product=product -> this is for specifying the product which the particular variation belongs to. 'product' is the field name in variation model and it is assigned to the 'product' variable here in this view.
                    product_variation.append(variation)#to store these values in CartItem
                except:
                    pass
        try:
            cart = Cart.objects.get(cart_id = _CartId(request)) #get the cart using the cart_id(present in the session)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _CartId(request)
            )
        cart.save()
        is_cart_item_exists = CartItem.objects.filter(product=product,cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product,cart=cart)
            #existing variations ->database
            #current variation->product_variation_list
            #item id->database
            #if current variation present inside the existing variation -> just increment the quantity
            existing_variations_list=[]
            id=[]
            for item in cart_item:
                existing_variation=item.variations.all()
                existing_variations_list.append(list(existing_variation))
                id.append(item.id)
            print(existing_variations_list)

            if product_variation in existing_variations_list:
                #increase_cart_item_id
                index = existing_variations_list.index(product_variation)
                item_id=id[index]
                item=CartItem.objects.get(product=product,id=item_id)
                item.quantity += 1
                item.save()

            else:
                item = CartItem.objects.create(product=product,quantity=1,cart=cart,)
            #check if the product_variation list is empty or not, if it is empty then we are just going to update the quantity and if it is not empty we are going to add the item to the database
                if len(product_variation)>0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(product=product,quantity=1,cart=cart)
            if len(product_variation)>0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
    # when we put products into the cart , the product becomes cart item.
def remove_cart(request,product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
        else:
            cart =  Cart.objects.get(cart_id=_CartId(request))
            cart_item = CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request,product_id,cart_item_id):
    product = get_object_or_404(Product,id = product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_CartId(request))
        cart_item = CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
    cart_item.delete()
    return redirect('cart')
def cart(request,total=0,quantity=0,cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user,is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _CartId(request))
            cart_items = CartItem.objects.filter(cart = cart,is_active = True)
        for cart_item in cart_items:
            total += (cart_item.product.price*cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2*total)/100
        grand_total=tax + total
    except ObjectDoesNotExist:
        pass
    return render(request, 'carts/cart.html',{'total':total,'quantity':quantity,'cart_items':cart_items,'tax':tax,'grand_total':grand_total})

@login_required(login_url='login')
def checkout(request,total=0,quantity=0,cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user,is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _CartId(request))
            cart_items = CartItem.objects.filter(cart = cart,is_active = True)
        for cart_item in cart_items:
            total += (cart_item.product.price*cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2*total)/100
        grand_total=tax + total
    except ObjectDoesNotExist:
        pass
    return render(request, 'carts/checkout.html',{'total':total,'quantity':quantity,'cart_items':cart_items,'tax':tax,'grand_total':grand_total})
