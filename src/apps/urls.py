from django.conf import settings
from django.conf.urls import patterns, include, url

import django.contrib.admin

django.contrib.admin.autodiscover()


urlpatterns = patterns('',

    # FIXME mapping root endpoint to admin_home for now
    url(r'^$', 'apps.admin.views.home', name='admin_home'),

    url(r'^', include('apps.website.urls', namespace='website')),
    url(r'^admin/', include('apps.admin.urls', namespace='admin')),
    url(r'^django_admin/', include(django.contrib.admin.site.urls)),
    url(r'^api/', include('apps.api.urls', namespace='api')),
)

urlpatterns += patterns('',
    url(r'^download/android', 'apps.foundation.views.download_android_view'),
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', dict(document_root=settings.MEDIA_ROOT)),
    )
