#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Django
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.simple import redirect_to
from django.contrib import messages
from django.template import Context, Template

import models
from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.contrib.gis import geos
from django.conf import settings

#settings.OL_API = settings.STATIC_URL + 'bud_arp/js/OpenLayers.js'

from olwidget.widgets import InfoMap

#from django.contrib.gis.utils import add_postgis_srs
#add_postgis_srs(900913)

TUTORS_GROUP = 'Tutors G2007'
CLASS_GROUP = 'g2007_ch'

def gu(username):
    """
    Gibt den Benutzer User mit dem Namen username zurück
    """
    return User.objects.get(username=username)

def index(request):
        
    groups = Group.objects.filter(name__in = [CLASS_GROUP, TUTORS_GROUP])
    last_online = User.objects.filter(groups__in = groups).order_by('-last_login')[:6]
    
    info_list = []
    tutor_img = settings.STATIC_URL + 'g2007.ch/teacher.png'

    persons = models.About.objects.all()
    random_aboutus = models.About.objects.filter(public=True, user__groups__name__in = [CLASS_GROUP]).order_by('?')[0]
    
    for person in persons:
        if person.is_student():
            html = """
            <div class="bubble">
                <h2><a href="{{ abs_url }}">{{ full_name }}</a></h2>
                    <a href="{{ abs_url }}"><img alt="Zum Profil von {{ full_name }}" title="Zum Profil von {{ full_name }}" src="{{ img }}" /></a>
                    <small><a href="{{ abs_url }}">Informationen anzeigen</a></small>
                <h3>Herkunft</h3>
                    <small>{{ location }}</small>
            {% if komp %}
                <h3>Funktion(en)</h3>
                <p>{{ komp|join:", " }}</p>
            {% endif %}
            </div>
            """
            t = Template(html)
            c = Context({
                'full_name':person, 
                'abs_url': person.get_absolute_url(), 
                'img': person.portrait.url_100x100, 
                'location':person.location_text, 
                'komp' : person.competences.all()
                })
            tmp = [person.origin, {
                'html': t.render(c), 
                'style': {
                   'fill_color': "#E7E7E7",
                   'stroke_color': "#0299FE",
                   'fill_opacity': 0.6,
                   'point_radius': 10,
                   },
                }]
        else:
            html = """
            <div class="bubble">
                <h2><a href="{{ abs_url }}">{{ full_name }}</a></h2>
                <a href="{{ abs_url }}"><img alt="Zum Profil von {{ full_name }}" title="Zum Profil von {{ full_name }}" src="{{ img }}" /></a>
                <small><a href="{{ abs_url }}">Informationen über unseren Dozenten <b>{{ full_name }}</b></a></small>
                <h3>Fächer</h3>
                <p>{{ faecher|join:", " }}</p>
            </div>
                """
            t = Template(html)
            c = Context({
                'full_name':person, 
                'abs_url': person.get_absolute_url(), 
                'faecher' : person.competences.all(), 
                'img':tutor_img})
            tmp = [person.origin, {
                'html': t.render(c),
                'style': {
                    'fill_color':'#0299FE',
                    'point_radius': 10,
                    },
                }]
        info_list.append(tmp)
        
    centroid = models.About.objects.filter(public=True, user__groups__name__in = [CLASS_GROUP]).collect().envelope.centroid 

    map_options = {
                   # Change cluster, default* und zoom_to_extend falls 
                   # http://groups.google.com/group/olwidget/browse_thread/thread/3351c09d0faa5e1
                   # behoben
                   #http://www.openstreetmap.org/?lat=47.29&lon=8.16&zoom=8&layers=B000FTF
                   'name':'Das g2007',
                   #'layers': ['osm.cloudmade','osm.mapnik'],
                   'layers': ['osm.mapnik'],
                   'cluster':True,
                   'map_div_style':{'width': '550px', 'height': '600px'},
                   #'map_options':{'controls':['LayerSwitcher', 'Navigation', 'PanZoom', 'Attribution', 'NavigationHistory'],},
                   'default_zoom':6,
                   'default_lat':centroid.y,
                   'default_lon':centroid.x,
                   'popup_pagination_separator':' von ',
                   'zoom_to_data_extent':False,
                   'overlay_style':{'point_radius':15, 'fill_color': "#000000", 'stroke_color': "#0299FE",'fill_opacity': 0.6,'stroke_linecap':'square'},
                   'cluster_style':{'font_size':14, },
                   }
    
    map = InfoMap(info_list, options=map_options)

    
    sitzplatz_matrix = [
                        [gu('lerch'), gu('berger'), gu('bassi'), None, gu('widmann'), gu('ruediger'), gu('kaiser')],
                        [gu('kohler'), gu('meister'), gu('staeheli'), None, gu('oggier'), gu('imoberdorf'), gu('wuersten')],
                        [gu('christian'), gu('schrattner'), gu('meier'), None, gu('walch'), gu('wuethrich'), gu('gredig')],
                        [gu('schaefer'), None, gu('farrer'), None, None, None, None ],
                        ]

        
    return render_to_response('aboutus/index2.html', 
                              locals(), 
                              context_instance=RequestContext(request))
    
def details(request, slug):
    obj = get_object_or_404(models.About, slug=slug, user__groups__name = CLASS_GROUP)
    if not len(obj.biography_set.all()):
        text = _('About %s...') % obj.user.get_full_name()
        bio = models.Biography.objects.create(about=obj, text=text)
        msg = _('New biography createt for %s') % obj.user.get_full_name() 
        #Es wurde eine neue Biographie für %s angelegt
        messages.add_message(request, messages.INFO, msg)
    else:
        bio = models.Biography.objects.get(about=obj)
    bth = models.BachelorThesis.objects.filter(authors__in = [obj])
        
    if request.user == obj.user:
        url_bio = reverse('admin:aboutus_biography_change', args=(bio.id,))
        url_about = reverse('admin:aboutus_about_change', args=(obj.id,))
        text = _(u'Hallo %s, du kannst deine <a href="%s">Biographie</a> und deine <a href="%s">persönlichen Informationen + Herkunft</a> im Admin-Bereich ändern') % (obj.user.get_full_name(), url_bio, url_about)
        messages.add_message(request, messages.INFO, text)
        
    
    return render_to_response('aboutus/details.html', 
                              locals(), 
                              context_instance=RequestContext(request))
    
def details_username(request, user):
    #obj, created = models.About.objects.get_or_create(user__username=user, defaults={'origin':geos.Point((8,50))})
    #if created:
    #    msg = u'Es wurde eine neues About für %s angelegt' % obj.user.get_full_name()
    obj = get_object_or_404(models.About, user__username=user)
    return redirect_to(request, url=obj.get_absolute_url(), permanent=False)
    
def tutors(request):
    tutors = models.About.objects.filter(user__groups__name = TUTORS_GROUP)
    return render_to_response('aboutus/tutors.html', 
                              locals(), 
                              context_instance=RequestContext(request))
