from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer
from restless.exceptions import BadRequest, NotFound

from django.db import IntegrityError
from django.conf import settings

from iclinic_webservices.webservices.zipcodes.models import ZipCode
from iclinic_webservices.webservices.apikeys.models import ApiKey
from iclinic_webservices.webservices.zipcodes.retriever import ZipCodeRetriever

from iclinic_webservices.webservices.zipcodes.exceptions import InvalidZipCodeFormatException, PostmonZipCodeNotFound


class ZipCodeResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'city': 'city',
        'state': 'state',
        'address': 'address',
        'zip_code': 'zip_code',
        'neighborhood': 'neighborhood'
    })

    def is_debug(self):
        return settings.DEBUG

    def is_authenticated(self):
        try:
            api_key = ApiKey.objects.get(key=self.request.GET.get('api_key'))
            if api_key.active:
                return True
            else:
                return False
        except ApiKey.DoesNotExist:
            return False

    def list(self):
        return ZipCode.objects.all()

    def create(self):
        zip_code = self.data.get('zip_code')

        try:
            retriever = ZipCodeRetriever(zip_code)
            data = retriever.fetch()
        except InvalidZipCodeFormatException:
            raise BadRequest("Invalid %s zip code format." % zip_code)
        except PostmonZipCodeNotFound:
            raise BadRequest("Zipcode %s not found in Postmon." % zip_code)

        zip_code_data = {
            'city': data.get('cidade'),
            'state': data.get('estado'),
            'zip_code': data.get('cep'),
            'address': data.get('logradouro'),
            'neighborhood': data.get('bairro')
        }

        try:
            zip_code_object = ZipCode.objects.create(**zip_code_data)
        except IntegrityError:
            raise BadRequest("Zipcode %s is already in the database." % zip_code)

        return zip_code_object

    def detail(self, pk):
        zip_code = pk

        try:
            zip_code_object = ZipCode.objects.get(zip_code=zip_code)
        except ZipCode.DoesNotExist:
            raise NotFound("Zipcode %s not found in the database." % zip_code)

        return zip_code_object

    def delete(self, pk):
        zip_code = pk

        try:
            zip_code_object = ZipCode.objects.get(zip_code=zip_code)
        except ZipCode.DoesNotExist:
            raise NotFound("Zipcode %s not found in the database." % zip_code)

        zip_code_object.delete()
