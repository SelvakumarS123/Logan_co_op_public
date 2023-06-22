from django.http import HttpResponse
from django.shortcuts import render
from store.models import Product,ReviewRating
def Home(request):
    products = Product.objects.all().filter(is_available=True).order_by('created_date')
    for product in products:
        reviews = ReviewRating.objects.filter(product_id = product.id , status =  True)

    return render(request, 'home.html', context={'products':products,'reviews': reviews,})

def my_custom_page_not_found_view(request,exception): #put in the request and also take in the exception(because if you reach this page, there has been some sort of error)
    return render(request,'error_page.html',status = 404) #status reports back the status to urls.py where this(status) will be handled