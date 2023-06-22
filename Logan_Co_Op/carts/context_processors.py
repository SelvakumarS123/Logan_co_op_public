from .models import Cart,CartItem
from .views import _CartId
def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return()
    else:
        try:
            cart = Cart.objects.filter(cart_id=_CartId(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])# we need only one result
            for cart_item in cart_items:
                cart_count +=cart_item.quantity
        except Cart.DoesNotExist:
            cart_count=0
    return dict(cart_count=cart_count)