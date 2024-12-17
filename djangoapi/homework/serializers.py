from rest_framework import serializers
from .models import BaiTap, NopBaiTap

class BaiTapSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaiTap
        fields = ('idbaitap', 'tenbaitap', 'mota', 'filebaitap', 'han_nop', 'ngaytao', 'idlophoc')

class NopBaiTapSerializer(serializers.ModelSerializer):
    class Meta:
        model = NopBaiTap
        fields = ('idnopbai', 'idbaitap', 'idsinhvien', 'filebaigiai', 'description', 'ngaynop', 'diem')
