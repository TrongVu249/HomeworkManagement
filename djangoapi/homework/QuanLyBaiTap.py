from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from django.shortcuts import get_object_or_404
from .models import BaiTap, NopBaiTap, LopHoc
from .serializers import BaiTapSerializer, NopBaiTapSerializer
import random, string
import datetime
import traceback
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

def is_valid_param(param) :
    return param != " " and param is not None and param != ""


def id_generator (size, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class ManageBaiTap(APIView):
    # 1. Tạo bài tập mới
    def post(self, request, format=None):
        try:
            # Lấy dữ liệu từ request
            data = request.data
            user = request.user

            # Kiểm tra quyền của giáo viên
            if not user.is_teacher:
                return Response(
                    {
                        'code': 1009,
                        'message': 'User does not have necessary permission'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # Kiểm tra id lớp học (idlop) có tồn tại hay không
            idlop = data.get('idlop')
            if not LopHoc.objects.filter(idlophoc=idlop).exists():
                return Response(
                    {
                        'code': 1004,
                        'message': 'Class ID not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Tạo ID bài tập duy nhất
            while True:
                idbaitap = id_generator()
                if not BaiTap.objects.filter(idbaitap=idbaitap).exists():
                    break

            # Lấy các trường dữ liệu đầu vào
            tenbaitap = data.get('tenbaitap')
            mota = data.get('mota')
            han_nop = data.get('han_nop')
            filebaitap = data.get('filebaitap')

            # Kiểm tra tên bài tập hợp lệ
            if not is_valid_param(tenbaitap) or len(tenbaitap) > 100:
                return Response(
                    {
                        'code': 1004,
                        'message': 'Invalid assignment name. Must be less than 100 characters.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra hạn nộp bài hợp lệ
            if han_nop:
                han_nop_date = datetime.datetime.strptime(han_nop, "%Y-%m-%d %H:%M:%S")
                if han_nop_date < datetime.datetime.now():
                    return Response(
                        {
                            'code': 1004,
                            'message': 'Deadline must not be in the past.'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {
                        'code': 1004,
                        'message': 'Deadline is required.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Tạo và lưu bài tập mới vào database
            baitap = BaiTap.objects.create(
                idbaitap=idbaitap,
                tenbaitap=tenbaitap,
                mota=mota,
                filebaitap=filebaitap,
                han_nop=han_nop_date,
                ngaytao=datetime.datetime.now(),
                idlop_id=idlop
            )

            # Serialize dữ liệu và phản hồi kết quả
            serializer = BaiTapSerializer(baitap)
            return Response(
                {
                    'code': 1000,
                    'message': 'Assignment created successfully.',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {
                    'code': 5000,
                    'message': 'An error occurred while creating the assignment.',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    # 2. Chỉnh sửa bài tập
    def put(self, request):
        try: 
            # Kiểm tra quyền của người dùng (phải là giáo viên)
            user = request.user
            if not user.is_teacher:
                return Response(
                    {
                        'code': 1009,
                        'message': 'User does not have necessary permission'
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Lấy dữ liệu từ request
            data = request.data
            idbaitap = data.get('idbaitap')

            # Kiểm tra ID bài tập có được cung cấp không
            if not is_valid_param(idbaitap):
                return Response(
                    {
                        'code': 1004,
                        'message': 'Missing assignment ID. Please add input'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra bài tập có tồn tại không
            try:
                baitap = BaiTap.objects.get(idbaitap=idbaitap)
            except BaiTap.DoesNotExist:
                return Response(
                    {
                        'code': 9992,
                        'message': 'Assignment not found. Please try again.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Lấy các trường dữ liệu mới
            tenbaitap = data.get('tenbaitap')
            mota = data.get('mota')
            han_nop = data.get('han_nop')
            filebaitap = data.get('filebaitap')

            # Kiểm tra tên bài tập hợp lệ
            if not is_valid_param(tenbaitap):
                return Response(
                    {
                        'code': 1006,
                        'message': 'Missing title info. Please add missing input'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Serialize dữ liệu cũ để kiểm tra thay đổi
            baitap_seria = BaiTapSerializer(baitap)
            old_tenbaitap = baitap_seria.data.get('tenbaitap')
            old_mota = baitap_seria.data.get('mota')
            old_han_nop = baitap_seria.data.get('han_nop')
            old_filebaitap = baitap_seria.data.get('filebaitap')

            # Kiểm tra dữ liệu mới có thay đổi không
            if (old_tenbaitap == tenbaitap and 
                old_mota == mota and 
                old_han_nop == han_nop and 
                old_filebaitap == filebaitap):
                return Response(
                    {
                        'code': 1012,
                        'message': 'No information has been modified'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra độ dài mô tả
            if is_valid_param(mota) and len(mota) > 200:
                return Response(
                    {
                        'code': 1013,
                        'message': 'The description is too long for the input field.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Cập nhật dữ liệu mới cho bài tập
            baitap.tenbaitap = tenbaitap
            baitap.mota = mota if is_valid_param(mota) else baitap.mota
            baitap.han_nop = han_nop if is_valid_param(han_nop) else baitap.han_nop

            if is_valid_param(filebaitap):
                baitap.filebaitap = filebaitap

            baitap.save()

            # Serialize lại dữ liệu đã cập nhật
            updated_serializer = BaiTapSerializer(baitap)

            return Response(
                {
                    'code': 1000,
                    'message': 'Update success',
                    'Updated assignment info': updated_serializer.data
                },
                status=status.HTTP_202_ACCEPTED
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {
                    'error': 'Some exception happened',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # 3. Xóa bài tập
    def delete(self, request):
        try:
            # Kiểm tra quyền của người dùng (phải là giáo viên)
            user = request.user
            if not user.is_teacher:
                return Response(
                    {
                        'code': 1009,
                        'message': 'User does not have necessary permission'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # Lấy ID bài tập từ request
            data = request.data
            idbaitap = data.get('idbaitap')

            # Kiểm tra ID bài tập có được cung cấp không
            if not is_valid_param(idbaitap):
                return Response(
                    {
                        'code': 1004,
                        'message': 'Missing assignment ID. Please add input'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra bài tập có tồn tại không
            if not BaiTap.objects.filter(idbaitap=idbaitap).exists():
                return Response(
                    {
                        'code': 9992,
                        'message': 'Assignment not found. Please try again.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Kiểm tra xem bài tập có sinh viên nộp bài hay không
            if NopBaiTap.objects.filter(idbaitap=idbaitap).exists():
                return Response(
                    {
                        'code': 1014,
                        'message': 'Cannot delete assignment. Students have already submitted their work.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Xóa bài tập
            baitap = BaiTap.objects.get(idbaitap=idbaitap)
            baitap.delete()

            return Response(
                {
                    'code': 1000,
                    'message': 'Assignment deleted successfully'
                },
                status=status.HTTP_202_ACCEPTED
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {
                    'code': 5000,
                    'error': 'Some exception happened',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # 4. Xem danh sách bài tập
    def get(self, request):
        try:
            # Lấy dữ liệu từ request
            data = request.data
            idlophoc = data.get('idlophoc')

            # Kiểm tra idlophoc có được cung cấp không
            if not idlophoc:
                return Response(
                    {
                        'code': 1004,
                        'message': 'Missing class ID. Please provide idlophoc.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra lớp học có tồn tại không
            if not LopHoc.objects.filter(idlophoc=idlophoc).exists():
                return Response(
                    {
                        'code': 1005,
                        'message': 'Class not found. Please try again.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Lấy thông tin lớp học
            lophoc = LopHoc.objects.get(idlophoc=idlophoc)
            tenlophoc = lophoc.tenlophoc

            # Lấy danh sách bài tập thuộc lớp học
            list_assignments = []
            assignments = BaiTap.objects.filter(idlop=idlophoc)
            assignment_serializer = BaiTapSerializer(assignments, many=True)

            for group in assignment_serializer.data:
                tenbaitap = group.get('tenbaitap')
                mota = group.get('mota')
                han_nop = group.get('han_nop')
                filebaitap = group.get('filebaitap')

                list_assignments.append(
                    {
                        "Ten bai tap": tenbaitap,
                        "Mo ta": mota,
                        "Han nop": han_nop,
                        "File bai tap": filebaitap,
                    }
                )

            # Trả về kết quả
            return Response(
                {
                    'code': 1000,
                    'message': "OK",
                    'Thong tin lop hoc': {
                        "Id lop hoc": idlophoc,
                        "Ten lop hoc": tenlophoc
                    },
                    'Danh sach bai tap': list_assignments
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': 'Something went wrong!'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    # 5. Lấy thông tin bài tập
    def get(self, request):
        try:
            # Lấy dữ liệu từ request
            data = request.data
            idbaitap = data.get('idbaitap')

            # Kiểm tra idbaitap có được cung cấp không
            if not is_valid_param(idbaitap):
                return Response(
                    {
                        'code': 1004,
                        'message': 'Missing assignment ID. Please add input.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra xem bài tập có tồn tại không
            if not BaiTap.objects.filter(idbaitap=idbaitap).exists():
                return Response(
                    {
                        'code': 9992,
                        'message': 'Assignment not found. Please try again.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Lấy thông tin chi tiết bài tập
            baitap = BaiTap.objects.get(idbaitap=idbaitap)
            baitap_serializer = BaiTapSerializer(baitap)

            # Trả về kết quả
            return Response(
                {
                    'code': 1000,
                    'message': 'OK',
                    'Thong tin chi tiet bai tap': baitap_serializer.data,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Xử lý lỗi hệ thống
            traceback.print_exc()
            return Response(
                {
                    'error': 'Some exception happened.',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GradeBaiTap(APIView):
    # 6. Lấy danh sách bài nộp của sinh viên
    def get(self, request):
        """
        Lấy danh sách bài nộp của sinh viên theo ID bài tập.
        Chỉ giáo viên được phép truy cập.
        """
        try:
            # Kiểm tra quyền của người dùng (phải là giáo viên)
            user = request.user
            if (not user.is_teacher):
                return Response(
                    {
                        'code' : 1009,
                        'message': 'User does not have necessary permission' 
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Lấy ID bài tập từ query parameters
            idbaitap = request.query_params.get('idbaitap')

            # Kiểm tra ID bài tập hợp lệ
            if not is_valid_param(idbaitap):
                return Response(
                    {"code": 1004, "message": "Missing assignment ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra bài tập có tồn tại không
            if not BaiTap.objects.filter(idbaitap=idbaitap).exists():
                return Response(
                    {"code": 1005, "message": "Assignment not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Lấy danh sách bài nộp cho bài tập
            submissions = NopBaiTap.objects.filter(idbaitap=idbaitap)
            serializer = NopBaiTapSerializer(submissions, many=True)

            return Response(
                {"code": 1000, "message": "Submissions retrieved successfully.", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"code": 5000, "message": "An error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        """
        Chấm điểm bài nộp của sinh viên.
        Chỉ giáo viên được phép thực hiện.
        """
        try:
            # Kiểm tra quyền của người dùng (phải là giáo viên)
            user = request.user
            if (not user.is_teacher):
                return Response(
                    {
                        'code' : 1009,
                        'message': 'User does not have necessary permission' 
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Lấy dữ liệu từ request
            data = request.data
            idnopbai = data.get('idnopbai')
            diem = data.get('diem')

            # Kiểm tra ID bài nộp hợp lệ
            if not is_valid_param(idnopbai):
                return Response(
                    {"code": 1004, "message": "Missing submission ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra bài nộp có tồn tại không
            try:
                submission = NopBaiTap.objects.get(idnopbai=idnopbai)
            except NopBaiTap.DoesNotExist:
                return Response(
                    {"code": 1005, "message": "Submission not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Kiểm tra điểm hợp lệ (từ 0 đến 10)
            if diem is None or not (0 <= float(diem) <= 10):
                return Response(
                    {"code": 1006, "message": "Invalid score. Score must be between 0 and 10."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Cập nhật điểm cho bài nộp
            submission.diem = diem
            submission.save()

            # Serialize kết quả
            serializer = NopBaiTapSerializer(submission)
            return Response(
                {"code": 1000, "message": "Score updated successfully.", "data": serializer.data},
                status=status.HTTP_202_ACCEPTED
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"code": 5000, "message": "An error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubmitBaiTap(APIView):
    # 7. Sinh viên nộp bài tập
    def post(self, request):
        try:
            data = request.data
            idbaitap = data.get('idbaitap')
            idsinhvien = data.get('idsinhvien')
            filebaigiai = data.get('filebaigiai')  # File bài làm
            description = data.get('description')  # Mô tả văn bản bài làm

            # 1. Kiểm tra ID bài tập có hợp lệ không
            if not BaiTap.objects.filter(idbaitap=idbaitap).exists():
                return Response(
                    {"code": 1004, "message": "Invalid assignment ID."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 2. Kiểm tra ID sinh viên có hợp lệ không
            if not SinhVien.objects.filter(idsinhvien=idsinhvien).exists():
                return Response(
                    {"code": 1005, "message": "Invalid student ID."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 3. Lấy thông tin bài tập để kiểm tra deadline
            baitap = BaiTap.objects.get(idbaitap=idbaitap)
            if timezone.now() > baitap.han_nop:
                return Response(
                    {"code": 1006, "message": "Deadline has passed. Submission not allowed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. Kiểm tra xem sinh viên đã nộp bài chưa
            if NopBaiTap.objects.filter(idbaitap=idbaitap, idsinhvien=idsinhvien).exists():
                return Response(
                    {"code": 1014, "message": "You have already submitted this assignment."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 5. Phân biệt 2 trường hợp: Nộp file và nộp văn bản
            if filebaigiai:
                # Trường hợp nộp file
                idnopbai = id_generator()
                nopbai = NopBaiTap.objects.create(
                    idnopbai=idnopbai,
                    idbaitap=baitap,
                    idsinhvien=SinhVien.objects.get(idsinhvien=idsinhvien),
                    filebaigiai=filebaigiai
                )
                serializer = NopBaiTapSerializer(nopbai)
                return Response(
                    {
                        "code": 1000,
                        "message": "File submission successful.",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

            elif is_valid_param(description):
                # Trường hợp nộp văn bản
                idnopbai = id_generator()
                nopbai = NopBaiTap.objects.create(
                    idnopbai=idnopbai,
                    idbaitap=baitap,
                    idsinhvien=SinhVien.objects.get(idsinhvien=idsinhvien),
                    description=description
                )
                serializer = NopBaiTapSerializer(nopbai)
                return Response(
                    {
                        "code": 1001,
                        "message": "Text submission successful.",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

            else:
                # Không có file và không có mô tả
                return Response(
                    {
                        "code": 1007,
                        "message": "Either file or description must be provided."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"code": 5000, "message": "An error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
