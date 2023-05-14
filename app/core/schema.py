import graphene
from graphene_django import DjangoObjectType
from app.permissions import paginate, is_authenticated, get_query
from django.db.models import Q
from core.models import (
    Product, ProductImage, Category,
    Order, OrderItem, ProductReview,
    Cart, CartItem, Coupon, Address
)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product


class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category


class OrderType(DjangoObjectType):
    class Meta:
        model = Order


class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem


class ProductReviewType(DjangoObjectType):
    class Meta:
        model = ProductReview


class CartType(DjangoObjectType):
    class Meta:
        model = Cart


class CartItemType(DjangoObjectType):
    class Meta:
        model = CartItem


class CouponType(DjangoObjectType):
    class Meta:
        model = Coupon


class AddressType(DjangoObjectType):
    class Meta:
        model = Address


class Query(graphene.ObjectType):
    categories = graphene.List(CategoryType, name=graphene.String())
    products = graphene.Field(paginate(ProductType),
                              search=graphene.String(),
                              min_price=graphene.Float(),
                              max_price=graphene.Float(),
                              category=graphene.String(),
                              sort_by=graphene.String(),
                              is_asc=graphene.Boolean()
                              )

    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    carts = graphene.List(CartType, name=graphene.String())

    def resolve_categories(self, info, name=False):
        query = Category.objects.prefetch_related("product_categories")

        if name:
            query = query.filter(Q(name__icontains=name) |
                                 Q(name__iexact=name)).distinct()

        return query

    def resolve_products(self, info, **kwargs):

        mine = kwargs.get("mine", False)
        if mine and not info.context.user:
            raise Exception("User auth required")

        query = Product.objects.select_related(
            "category", "brand", "supplier").prefetch_related(
            "product_images", "product_carts"
        )

        if kwargs.get("search", None):
            qs = kwargs["search"]
            search_fields = (
                "name", "description", "category__name"
            )

            search_data = get_query(qs, search_fields)
            query = query.filter(search_data)

        if kwargs.get("min_price", None):
            qs = kwargs["min_price"]

            query = query.filter(Q(price__gt=qs) | Q(price=qs)).distinct()

        if kwargs.get("max_price", None):
            qs = kwargs["max_price"]

            query = query.filter(Q(price__lt=qs) | Q(price=qs)).distinct()

        if kwargs.get("category", None):
            qs = kwargs["category"]

            query = query.filter(Q(category__name__icontains=qs)
                                 | Q(category__name__iexact=qs)).distinct()

        if kwargs.get("sort_by", None):
            qs = kwargs["sort_by"]
            is_asc = kwargs.get("is_asc", False)
            if not is_asc:
                qs = f"-{qs}"
            query = query.order_by(qs)

        return query

    def resolve_product(self, info, id):
        query = Product.objects.select_related("category").prefetch_related(
            "product_images", "product_comments", "product_carts"
        ).get(id=id)

        return query

    @is_authenticated
    def resolve_carts(self, info, name=False):
        query = Cart.objects.select_related(
            "user", "product").filter(user_id=info.context.user.id)

        if name:
            query = query.filter(Q(product__name__icontains=name) | Q(
                product__name__iexact=name)).distinct()

        return query


class ProductInput(graphene.InputObjectType):
    name = graphene.String()
    price = graphene.Float()
    description = graphene.String()
    category_id = graphene.ID()
    brand_id = graphene.ID()
    supplier_id = graphene.ID()


class ProductImageInput(graphene.InputObjectType):
    image_id = graphene.ID(required=True)
    is_cover = graphene.Boolean()


class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)

    class Arguments:
        product_data = ProductInput(required=True)
        stock = graphene.Int(required=True)
        images = graphene.List(ProductImageInput)

    @is_authenticated
    def mutate(self, info, stock, product_data, images, **kwargs):

        product_data["stock"] = stock

        product = Product.objects.create(**product_data, **kwargs)

        ProductImage.objects.bulk_create([
            ProductImage(
                product_id=product.id, **image_data
            ) for image_data in images
        ])

        return CreateProduct(
            product=product
        )


class Mutation(graphene.ObjectType):
    create_product = CreateProduct.Field()
