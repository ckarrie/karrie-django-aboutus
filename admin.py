#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.gis import admin
from django.utils.translation import ugettext as _
from django.contrib import messages
import models

# Workaround Django 1.3.0 --> 1.4.0 alpha
try:
    GeoAdmin = admin.OSMGeoAdmin
except AttributeError, e:
    GeoAdmin = admin.GeoModelAdmin

#from reversion import helpers

error_msg   = u'Böser %(r_user)s, das gehört %(obj_user)s!!! - Das Objekt wurde zurückgesetzt.'
info_msg    = u'<span class="errornote">Bitte nicht ändern! Bringt nichts. Glaubs doch einfach... -- Christian</span>'

class AboutAdmin(GeoAdmin):
    #list_display = ('user', 'slug', 'hobby_tags', 'is_student', 'is_tutor','last_modified',)
    list_display = ('user', 'slug', 'is_student', 'is_tutor','last_modified',)
    #list_display = ('user', 'slug', 'is_student', 'is_tutor','last_modified','location_text',)
    #list_editable = ('hobby_tags',)
    #list_editable = ('location_text',)
    fieldsets = (
        (None, {
            #'fields': ('location_text', 'origin', 'portrait', 'hobby_tags')
            'fields': ('location_text', 'origin', 'portrait',)
        }),
        (_('Advanced options'), {
            'classes': ('collapse',),
            'fields': ('competences', 'ref_websites',)
        }),
        (_('User'), {
            'classes':('collapse',),
            'fields':('slug', 'user','public',),
            'description':info_msg
        }))
    
    #list_filter = ('hobby_tags', 'last_modified',)
    list_filter = ('last_modified',)
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'user__username']
            
    def queryset(self, request):
        if request.user.is_superuser:
            qs = self.model._default_manager.all()
        else:
            qs = self.model._default_manager.filter(user=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if request.user != obj.user:
                msg = error_msg % {'r_user'  : request.user.get_full_name(), 
                                   'obj_user': obj.user.get_full_name()}
                messages.add_message(request, messages.ERROR, msg)
                obj.user = request.user
        obj.save()

    
class BachelorThesisAdmin(GeoAdmin):
    #list_display = ('title','tags',)
    list_display = ('title',)
    #list_editable = ('tags',)
    readonly_fields = ('slug',)
    
    
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('url', 'descr')
    
class BiographyAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('text', )
        }),
        (_('Advanced options'), {
            'classes': ('collapse',),
            'fields': ('about', ),
            'description':info_msg
        }),)
    
    def queryset(self, request):
        if request.user.is_superuser:
            qs = self.model._default_manager.all()
        else:
            qs = self.model._default_manager.filter(about__user=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if request.user != obj.about.user:
                msg = error_msg % {'r_user'  : request.user.get_full_name(), 
                                   'obj_user': obj.about.user.get_full_name()}
                messages.add_message(request, messages.ERROR, msg)
                user = About.objects.get(user=request.user)
                obj.about = user
        obj.save()



admin.site.register(models.About, AboutAdmin)
admin.site.register(models.Competence)
admin.site.register(models.Reference, ReferenceAdmin)
admin.site.register(models.Biography, BiographyAdmin)
admin.site.register(models.BachelorThesis, BachelorThesisAdmin)

#helpers.patch_admin(models.About)
#helpers.patch_admin(models.Competence)
#helpers.patch_admin(models.Reference)
#helpers.patch_admin(models.Biography)
#helpers.patch_admin(models.BachelorThesis)
