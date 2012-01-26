#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.gis.db import models
from django.contrib.auth.models import User, Group
#from tagging.fields import TagField
#from tagging.models import Tag
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils import simplejson
from django.core.files import File
from django.conf import settings
import urllib
import thumbs 
import views

HTML_EXAMPLE = """
    <h4>Beispiel:</h4>
    <p>&lt;h4&gt;Lebenslauf&lt;/h4&gt;<br />
    &lt;p&gt;Geboren .... Schule ....&lt;/p&gt;<br />
    <br />
    &lt;h4&gt;Zukunfts(wunsch)&lt;/h4&gt;<br />
    &lt;p&gt;Erfolgreiches Arbeiten im Gebiet ....&lt;/p&gt;<br />
    <br />
    &lt;h4&gt;Motto&lt;/h4&gt;<br />
    &lt;p&gt;Basel und FSV! Oleee&lt;/p&gt;</p>"""

class Competence(models.Model):
    job = models.CharField(max_length = 100, help_text='Bezeichnung des Jobs. Z.B. <em>Geodäsie</em>')
    
    def __unicode__(self):
        return self.job
    
    def __str__(self):
        return self.job
    
    class Meta:
        ordering = ['job',]
        verbose_name = u"Job"
        verbose_name_plural = u"Jobs"
        
        
class Reference(models.Model):
    url = models.URLField(verify_exists=False, help_text='z.B. <em>http://meinetollewebsite.ch</em>')
    descr = models.TextField(max_length = 500, help_text='Kurze Beschreibung der Webseite', verbose_name = 'Beschreibung')
    
    def __unicode__(self):
        return self.url
        
    class Meta:
        verbose_name = u"Referenz-Webseite"
        verbose_name_plural = u"Referenz-Webseiten"
    
class About(models.Model):
    user = models.ForeignKey(User, help_text=u'Benutzer, dem diese <em>About-Seite</em> gehört', verbose_name = 'User')
    slug =  models.SlugField(blank=True, unique=True, null = True, help_text=u'Maschinenlesbare Bezeichnung. z.B. <em>alle-voegel-sind-schon-da</em>')
    origin = models.PointField(verbose_name = 'Herkunftsort', help_text=u'<h3>Anleitung Panel</h3>Mit der Hand die Karte bewegen, mit dem Stift den Punkt setzen.')
    portrait = thumbs.ImageWithThumbsField(verbose_name = 'Portrait Bild', upload_to = 'g2007.ch/portraits/', sizes=((100,100),(240,240)), null=True, blank=True)
    #hobby_tags = TagField(help_text=u'Kommagetrennt: z.B. <em>Ski fahren, Rodel, Äpfel essen, Ausgleichsrechnung</em> gehört')
    last_modified = models.DateTimeField(auto_now=True)
    competences = models.ManyToManyField(Competence, null=True, blank=True, help_text=u'Kompetenzen / Funktionen.')
    ref_websites = models.ManyToManyField(Reference, null=True, blank=True, help_text=u'Eigene Webseiten.')
    public = models.BooleanField(help_text=u'Öffentlich? <small>TODO: Mit robots.txt synchronisieren</small>', default=True)
    location_text = models.TextField(max_length=200, null=True, blank=True, help_text=u'Text wird automatisch durch die Position des Pins <a href="http://wiki.openstreetmap.org/wiki/Nominatim">reversed-geocodet</a>. Durch löschen des Textes und Abspeichern, wird bei veränderter Lage des Pins die Adresse erneut geo-reversed-codiert.')
    
    objects = models.GeoManager()
    
    def __unicode__(self):
        return self.user.get_full_name()
    
    def get_absolute_url(self):
        if self.is_student():
            return reverse(views.details, kwargs={'slug':self.slug})
        else:
            url = reverse(views.tutors) + "#%s" %self.user
            return url
        
    def save(self):
        if not len(self.slug):
            self.slug = slugify(self.user.get_full_name())
        if not self.portrait:
            no_pic_loc = settings.MEDIA_ROOT + '/g2007.ch/no_pic.jpg'
            f = File(open(no_pic_loc))
            self.portrait.save('no_pic.jpg', f, True)
        if not len(self.location_text):
            self.location_text = self.reverse_geocoded_location()
        super(About, self).save()
        
    def is_student(self):
        return not self.is_tutor()
    
    def is_tutor(self):
        tutors_grp, created = Group.objects.get_or_create(name="Tutors G2007")
        tutors = tutors_grp.user_set.all()
        return self.user in tutors
    
    def reverse_geocoded_location(self):
        wgs = self.origin.transform(4326, clone=True)
        lat = wgs.y
        lon = wgs.x
        text = u''
        params = urllib.urlencode({'format': 'json', 
                                   'lat': lat, 
                                   'lon': lon, 
                                   'zoom': 18, 
                                   'addressdetails': 1,
                                   'accept-language':'de'})
        try:
            f = urllib.urlopen("http://nominatim.openstreetmap.org/reverse?%s" % params).read()
            no_cc = f.lstrip('/* Data Copyright OpenStreetMap Contributors, Some Rights Reserved. CC-BY-SA 2.0. */\n')
            json = simplejson.loads(no_cc)
            json_address = json['address']
            
            #TODO: Verbessern, evtl. mit json_address.pop('country', None)
                        
            if json_address.has_key('country'):
                text += unicode(json_address['country']) + u' » '
            if json_address.has_key('county'):
                text += unicode(json_address['county']) + u' » '
            if json_address.has_key('state'):
                text += unicode(json_address['state']) + u' » '
            if json_address.has_key('city'):
                text += unicode(json_address['city']) + u' » '
            if json_address.has_key('town'):
                text += unicode(json_address['town']) + u' » '
            if json_address.has_key('village'):
                text += unicode(json_address['village']) + u' » '
            if json_address.has_key('road'):
                text += unicode(json_address['road'])
            #return json['address']
        except IOError:
            text = self.location_text
        
        return text      
            
    is_student.short_description = u'Student'
    is_tutor.short_description = u'Dozent'
    reverse_geocoded_location.short_description = u'Ort laut OSM'
        
    class Meta:
        ordering = ['last_modified',]
        verbose_name = u"Über uns"
        verbose_name_plural = u"Über uns"
        
class Biography(models.Model):
    text = models.TextField(help_text = u'HTML erlaubt. Höchste Überschrift ist h4. Siehe <a href="http://www.addedbytes.com/cheat-sheets/download/html-cheat-sheet-v1.png">kurze HTML Anleitung</a>.' + HTML_EXAMPLE)
    about = models.ForeignKey(About) 
    
    def __unicode__(self):
        return self.about.user.get_full_name()
    
    class Meta:
        ordering = ['about',]
        verbose_name = u"Biographie"
        verbose_name_plural = u"Biographien"    
        
class BachelorThesis(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, blank=True)
    sub_title = models.CharField(max_length=300)
    authors = models.ManyToManyField(About)
    tutors = models.ManyToManyField(User, blank=True)
    #tags = TagField()
    abstract = models.TextField(help_text = u'HTML erlaubt. Höchste Überschrift ist h4. Siehe <a href="http://www.addedbytes.com/cheat-sheets/download/html-cheat-sheet-v1.png">kurze HTML Anleitung</a>.' + HTML_EXAMPLE)
    published = models.DateField(blank=True)
    published_at = models.ManyToManyField(Reference)
    geolocation = models.MultiPointField(blank=True)
    objects = models.GeoManager()
    
    def __unicode__(self):
        return self.title   
    
    def save(self):
        if not len(self.slug):
            self.slug = slugify(self.title)
        super(BachelorThesis, self).save()
    
    class Meta:
        ordering = ['title',]
        verbose_name = u"Bachelor-Thesis"
        verbose_name_plural = u"Bachelor-Thesis"    

