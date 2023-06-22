from base64 import urlsafe_b64decode
from email import message
import email
from email.message import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from orders.models import OrderProduct
from orders.models import Order
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from carts.views import _CartId
from carts.models import Cart,CartItem
import requests

#verification email

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name'] # when using django forms, use cleaned data to fetch values from request
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            user=Account.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
            user.phone_number=phone_number
            user.save()
            #user activation
            current_site= get_current_site(request)
            mail_subject = "Activate your account-Logan Co-Op"
            message = render_to_string('accounts/account_verification_mail.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)), #encoding the user id(pk) so that nobody can see the pk. when we are activationg the account it will be decoded.
                'token':default_token_generator.make_token(user),#create a token for this particular user
            })
            to_email = email
            send_email =EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            #messages.success(request,'Registraion Successful')
            UserProfile.objects.create(user=user)
            return redirect('/accounts/login/?command=verification&email='+email)

    else:
        form = RegistrationForm()
    return render(request,'accounts/register.html',{'form':form})
def login(request):
    if request.method == 'POST':
        email=request.POST['email']
        #print(email)
        password=request.POST['password']

        user = auth.authenticate(email=email,password=password) #will return the user object
        if user is not None:
            try: #check if there is any cart item
                cart = Cart.objects.get(cart_id=_CartId(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item=CartItem.objects.filter(cart=cart)#cart=cartId
                    #get the product variations by cart id
                    product_variation=[]
                    for item in cart_item:
                        variation=item.variations.all()
                        product_variation.append(list(variation))
                    #get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
                    existing_variations_list=[]
                    id=[]
                    for item in cart_item:
                        existing_variation=item.variations.all()
                        existing_variations_list.append(list(existing_variation))
                        id.append(item.id)
                    for pr in product_variation:
                        if pr in existing_variations_list:
                            index=existing_variations_list.index(pr)
                            item_id=id[index]
                            item=CartItem.objects.get(id=item_id)
                            item.quantity +=1
                            item.user=user
                            item.save()
                        else:
                            cart_item=CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user=user
                                item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'You are now Logged In')
            url=request.META.get('HTTP_REFERER') #WILL COLLECT AND STORE THE URLPATH WHERE YOU CAME FROM
            try:
                query=requests.utils.urlparse(url).query
                #query-> next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                #params-> {'next': '/cart/checkout/'}
                if 'next' in params:
                    next_page= params['next']
                    return redirect(next_page)
            except:
                return redirect('dashboard')
        else:
            messages.error(request,'Invalid LogIn Credentials')
            return redirect('login')
    return render(request,'accounts/login.html')

@login_required(login_url = 'login') #if you try tp log out without being logged in then it should take you to the login page
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are Logged Out')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode() #gives the pk of the user
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'WELCOME! Your Logan Co-Op account has been activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid Activation link')
        return redirect('register')

@login_required(login_url = 'login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered =True)
    orders_count = orders.count()
    userprofile=UserProfile.objects.get(user_id=request.user.id)
    context = {
        'orders_count':orders_count,
        'userprofile':userprofile,
    }
    return render(request,'accounts/dashboard.html', context=context)



def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            current_site= get_current_site(request)
            mail_subject = "Reset Your Password-Logan Co-Op"
            message = render_to_string('accounts/password_reset_mail.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)), #encoding the user id(pk) so that nobody can see the pk. when we are activationg the account it will be decoded.
                'token':default_token_generator.make_token(user),#create a token for this particular user
            })
            to_email = email
            send_email =EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, "We've emailed you with a link to reset your password")
            return redirect('passwordReset')
        else:
            messages.error(request, 'Account Does Not Exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')
def validatePasswordReset(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode() #gives the pk of the user
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid #save the id inside thesession
        messages.success(request, 'Reset your password~')
        return redirect('passwordReset')
    else:
        messages.error(request, 'This Link has been Expired')
        return redirect('login')
def passwordReset(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password==confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password) #set_password-> save the password in hashed format
            user.save()
            messages.success(request,'Your password has been succesfully reset.')
            return redirect('login')
        else:
            messages.error(request, "For God's sake try n remember the password for 5 secs man. Dayummmm.")
            return redirect('passwordReset')
    else:
        return render(request, 'accounts/passwordReset.html')

@login_required(login_url='login')
def myOrders(request):
    orders = Order.objects.filter(user=request.user, is_ordered = True).order_by('-created_at')

    return render(request, 'accounts/my_orders.html',{'orders':orders})

@login_required(login_url='login')
def editProfile(request): #handling 2 forms
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method=="POST":
        user_form = UserForm(request.POST , instance = request.user) #we're updating the form
        profile_form = UserProfileForm(request.POST, request.FILES, instance = userprofile)
        #if user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, 'Your Profile has been updated.')
        return redirect('editProfile')
    else:
        user_form = UserForm(instance=request.user) #by passing this instance we can see the existing data inside the form
        profile_form = UserProfileForm(instance=userprofile)
    context= {
        'user_form':user_form,
        'profile_form': profile_form,
        'userprofile': userprofile
    }
    return render(request, 'accounts/edit_profile.html', context=context)

@login_required(login_url='login')
def changePassword(request):
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_new_password']

        user = Account.objects.get(username__exact=request.user.username)
        if new_password == confirm_password:
            success = user.check_password(current_password) #use builtin method for checking password because the passwords are hashed
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your Password has been Updated.")
                #auth.logout(request)
                messages.success(request, "Please Login again.")
                return redirect('changePassword')
            if not success:
                messages.error(request, "Wrong Password. did you forget your password?")
                #return render(request, 'accounts/forgotPassword.html')
                return redirect('changePassword')
        else:
            messages.error(request, "Passwords doesn't match.")
            return redirect('changePassword')

    return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def orderDetail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number = order_id)
    order = Order.objects.get(order_number = order_id)
    sub_total = 0
    for i in order_detail:
        sub_total += i.product_price *i.quantity
    return render(request, 'accounts/order_detail.html', {'order_detail': order_detail, 'order':order ,'sub_total':sub_total})
