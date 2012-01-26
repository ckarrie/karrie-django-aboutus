#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 
        'karrie.django.aboutus.views.index'),

    url(r'^(?P<slug>[-\w]+)$', 
        'karrie.django.aboutus.views.details'),
        
    url(r'^r/(?P<user>[-\w]+)$', 
        'karrie.django.aboutus.views.details_username'),        
        
    url(r'^lehrer/$', 
        'karrie.django.aboutus.views.tutors'),        
)
