from django.db import models
from django.utils import timezone


#class LopHoc(models.Model):
#    idlophoc = models.CharField(max_length=10, primary_key=True)
#    tenlophoc = models.CharField(max_length=100)
#
#    def __str__(self):
#        return self.tenlophoc

#class SinhVien(models.Model):
#    idsinhvien = models.CharField(max_length=10, primary_key=True)
#    tensinhvien = models.CharField(max_length=100)
#
#    def __str__(self):
#        return self.tensinhvien

# Bảng quản lý Bài Tập
class BaiTap(models.Model):
    idbaitap = models.CharField(max_length=10, primary_key=True)  # ID bài tập
    tenbaitap = models.CharField(max_length=100)                 # Tên bài tập
    mota = models.TextField()                                    # Mô tả chi tiết bài tập
    filebaitap = models.FileField(upload_to='baitap_files/', null=True, blank=True)  # File đính kèm bài tập
    han_nop = models.DateTimeField()                             # Hạn nộp bài tập
    ngaytao = models.DateTimeField(default=timezone.now)         # Ngày tạo bài tập
    idlophoc = models.ForeignKey(LopHoc, on_delete=models.CASCADE)  # Liên kết lớp học

    def __str__(self):
        return f"{self.tenbaitap} - {self.idlop.tenlophoc}"

# Bảng quản lý Nộp Bài Tập
class NopBaiTap(models.Model):
    idnopbai = models.CharField(max_length=10, primary_key=True)  # ID nộp bài
    idbaitap = models.ForeignKey(BaiTap, on_delete=models.CASCADE, related_name='nopbai')  # Liên kết tới bài tập
    idsinhvien = models.ForeignKey(SinhVien, on_delete=models.CASCADE, related_name='nopbai')  # Liên kết sinh viên
    filebaigiai = models.FileField(upload_to='nopbai_files/')     # File bài giải sinh viên nộp
    description = models.TextField(null=True, blank=True)         # Mô tả bài làm (nếu không có file)
    ngaynop = models.DateTimeField(default=timezone.now)          # Ngày nộp bài
    diem = models.FloatField(null=True, blank=True)               # Điểm số bài tập (giáo viên chấm)

    def __str__(self):
        return f"{self.idsinhvien.tensinhvien} - {self.idbaitap.tenbaitap} - Điểm: {self.diem}"