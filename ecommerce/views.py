from django.shortcuts import render

items = [
    {
        'seller': 'Doga Yilmaz',
        'product_name': 'Rocket Appartamento Manual Espresso Machine',
        'description': 'Best espresso machine ever.'
    },
    {
        'seller': 'Sarp Sunar',
        'product_name': 'Rocket Coffee Grinder',
        'description': 'Sample description.'
    }
]


def home(request):
    context = {
        'title': 'Home',
        'items': items
    }
    return render(request, 'ecommerce/home.html', context)


def about(request):
    return render(request, 'ecommerce/about.html')
