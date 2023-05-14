from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _
from import_export.admin import ImportExportMixin
from users.models import User
from core.models import Category, Product, Brand, Supplier


class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (_('Important dates'), {'fields': ('last_login',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),
    )


class CategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'slug', 'name', 'description', 'parent']


class BrandAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'name']


class ProductAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'slug', 'name', 'description',
                    'price', 'stock', 'category', 'brand']


class SupplierAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'contact_email', 'phone']


admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Supplier, SupplierAdmin)
