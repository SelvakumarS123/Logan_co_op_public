from . models import Category


def menu_link(request): #fetch all the categories from the database
    links = Category.objects.all()
    return dict(links=links)