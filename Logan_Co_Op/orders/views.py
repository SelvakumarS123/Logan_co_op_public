import datetime
import json
from store.models import Product
from . models import Order, OrderProduct,Payment
from . forms import OrderForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.http import HttpResponse
from carts.models import CartItem
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# Create your views here.

def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered = False, order_number=body['orderID'])

    #print(body)
    #store trans details in payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid=order.order_total, 
        status = body['status'],
    )
    payment.save()
    order.payment=payment #inside the order model, we have a field named payment..fgs update that too
    order.is_ordered = True
    order.save()

    # move the cart items to order product table
    cart_items = CartItem.objects.filter(user = request.user)
    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id #line 14
        order_product.payment = payment #line 18
        order_product.user_id = request.user.id
        order_product.product_id = item.product_id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered=True #payment is already successful
        order_product.save() #this save will generate a id for the order_product
        #for storing the many to many field , you have to first save the object and then assign the value(you can't just assign like 'order_product.variations = item.variations'->wrong)
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        order_product = OrderProduct.objects.get(id=order_product.id)
        order_product.variations.set(product_variation)
        order_product.save()

        #reduce the quantity of the sold products

        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
    #clear cart (delete the cart items of this particular user)
    CartItem.objects.filter(user=request.user).delete()
    mail_subject = "Your Order Has Been Received-Logan Co-Op"
    message = render_to_string('orders/order_received_mail.html',{
        'user': request.user,
        'order':order
    })
    to_email = request.user.email
    send_email =EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()
    # send order number and transaction id back to sendData() method via jsonResponse
    data = {
        'order_number':order.order_number,
        'transID':payment.payment_id,
    }
    return JsonResponse(data) #data will be sent back to sendData()
    #return render(request, 'orders/payments.html')

def place_order(request, total=0, quantity=0,):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <=0:
        return redirect('store')
    grand_total=0
    tax=0
    for cart_item in cart_items:
        total += (cart_item.product.price*cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2*total)/100
    grand_total=tax + total
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            #store all billing info in Order table
            data = Order() #instance of this order
            data.user = current_user
            data.first_name=form.cleaned_data['first_name']
            data.last_name=form.cleaned_data['last_name']
            data.phone_number=form.cleaned_data['phone_number']
            data.email=form.cleaned_data['email']
            data.address_line_1=form.cleaned_data['address_line_1']
            data.address_line_2=form.cleaned_data['address_line_2']
            data.country=form.cleaned_data['country']
            data.state=form.cleaned_data['state']
            data.city=form.cleaned_data['city']
            data.order_note=form.cleaned_data['order_note']
            data.order_total=grand_total
            data.tax = tax
            data.ip=request.META.get('REMOTE_ADDR')
            data.save() #once we save, this will create a primary key(id number->used to create order id)
            #generate order number
            year = int(datetime.date.today().strftime('%Y'))
            date = int(datetime.date.today().strftime('%d'))
            month = int(datetime.date.today().strftime('%m'))
            d = datetime.date(year,month,date)
            current_date = d.strftime('%Y%m%d') #20220819
            order_number=current_date + str(data.id)
            data.order_number=order_number
            data.save()

            order = Order.objects.get(user = current_user, is_ordered=False, order_number=order_number)
            context={
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'tax':tax,
                'grand_total':grand_total,
            }
            return render(request, 'orders/payments.html', context=context)
        else:
            return redirect('cart')
    else:
        return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order=Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        subtotal=0
        for item in ordered_products:
            subtotal += item.product_price * item.quantity
        payment = Payment.objects.get(payment_id=transID)
        context={
            'order':order,
            'ordered_products':ordered_products, #check forloop in order_complete.html
            'order_number':order.order_number,
            'transID':payment.payment_id,
            'subtotal':subtotal,
            'payment':payment,
        }
        return render(request, 'orders/order_complete.html',context=context)
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
