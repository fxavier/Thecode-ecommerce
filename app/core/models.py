from django.db import models
from django.conf import settings
from django.db.models.signals import pre_save
from core import utils


class Category(models.Model):
    slug = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Product(models.Model):
    slug = models.SlugField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.ForeignKey(
        Category, related_name="product_categories", on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    def average_rating(self):
        reviews = self.productreview_set.all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            average_rating = total_rating / len(reviews)
            return average_rating
        return 0

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="product_images", on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to=utils.product_image_file_path)
    is_cover = models.BooleanField(default=False)


class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('provider', 'Provider'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    is_company = models.BooleanField(default=False)


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}, \
                 {self.postal_code}, {self.country}"


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def get_total_price(self):
        cart_items = self.cartitem_set.all()
        subtotal = sum(item.product.price *
                       item.quantity for item in cart_items)

        if self.coupon:
            discount = self.coupon.calculate_discount(subtotal)
        else:
            discount = 0

        taxes = subtotal * (self.tax_rate / 100)

        total_price = subtotal - discount + taxes
        return total_price


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="product_carts", on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} in {self.cart.user.username}'s Cart"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
    )
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address',
        on_delete=models.SET_NULL, null=True)
    billing_address = models.ForeignKey(
        Address, related_name='billing_address',
        on_delete=models.SET_NULL, null=True)

    def get_total_price(self):
        order_items = self.orderitem_set.all()
        subtotal = sum(item.product.price *
                       item.quantity for item in order_items)

        if self.coupon:
            discount = self.coupon.calculate_discount(subtotal)
        else:
            discount = 0

        taxes = subtotal * (self.tax_rate / 100)

        total_price = subtotal - discount + taxes
        return total_price


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="product_orders", on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    discount_type = models.CharField(max_length=20,
                                     choices=(('percentage', 'Percentage'),
                                              ('fixed', 'Fixed Amount'),
                                              ('shipping', 'Free Shipping')))
    discount_value = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    usage_limit = models.IntegerField(null=True, blank=True)

    def calculate_discount(self, amount):
        if self.discount_type == 'percentage':
            return amount * (self.discount_value / 100)
        elif self.discount_type == 'fixed':
            return self.discount_value
        elif self.discount_type == 'shipping':
            return 0
        return 0

    def __str__(self):
        return self.description


class Service(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField()
    availability = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class OrderService(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()

    def __str__(self):
        return self.order.user.name


class ShippingCarrier(models.Model):
    name = models.CharField(max_length=255)
    tracking_url = models.URLField()

    def __str__(self):
        return self.name


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    format = models.CharField(max_length=255)
    template = models.CharField(max_length=255)

    def __str__(self):
        return self.invoice_number


class ProductReview(models.Model):
    RATING_CHOICES = (
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"


def category_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = utils.unique_slug_generator(instance)


pre_save.connect(category_pre_save_receiver, sender=Category)


def product_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = utils.unique_slug_generator(instance)


pre_save.connect(product_pre_save_receiver, sender=Product)
