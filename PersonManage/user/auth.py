import hashlib
from django.conf import settings
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from PersonManage.user.models import User, UserInfo
from PersonManage.user.serializer import OneUser, LoginInfo
from redis import StrictRedis


class AuthView(APIView):
    def get(self, request):
        user = User.objects.filter(pk=request.u.id).first()
        if user:
            data = LoginInfo(instance=user, many=False).data
            return Response({'code': 200, 'msg': 'Get userinfo successfully!', 'data': data})
        return Response({'code': 400, 'msg': 'Data does not exist!', 'data': None})

    def post(self, request):
        try:
            mp = hashlib.md5()
            mp.update(request.data.get('password', '').encode('utf-8'))
            user = User.objects.filter(
                username=request.data.get('username'),
                password=mp.hexdigest()
            ).first()
            if user:
                if not user.activated:
                    return Response({'code': 401, 'msg': 'This account is not allowed to log in!', 'data': None})
                user.last_login = timezone.now()
                user.save()

                redis = StrictRedis(host=settings.DATABASES['redis']['HOST'],
                                    port=settings.DATABASES['redis']['PORT'],
                                    db=settings.DATABASES['redis']['NAME_1'],
                                    password=settings.DATABASES['redis']['PASS'])
                m = hashlib.md5()
                m.update(user.username.encode('utf-8'))
                token = m.hexdigest()
                redis.set(token, user.id)
                redis.expire(token, 3600)

                data = OneUser(instance=user, many=False).data
                data.update({'token': token})
                return Response({'code': 200, 'msg': 'Login successful!', 'data': data})
            return Response({'code': 400, 'msg': 'Wrong username or password!', 'data': None})
        except Exception as ex:
            return Response({'code': 500, 'msg': str(ex), 'data': None})

    def put(self, request):
        try:
            if user := User.objects.filter(pk=request.u.id).first():
                if 'phone' in request.data or 'email' in request.data:
                    if email := request.data.get('email'):
                        user.email = email
                    if phone := request.data.get('phone'):
                        user.phone = phone
                    if nickname := request.data.get('nickname'):
                        user.nickname = nickname
                    user.save()
                else:
                    if userinfo := UserInfo.objects.filter(user=user).first():
                        if name := request.data.get('name'):
                            userinfo.name = name
                        if age := request.data.get('age'):
                            userinfo.age = age
                        if sex := request.data.get('sex'):
                            userinfo.sex = sex
                        if birthday := request.data.get('birthday'):
                            userinfo.birthday = birthday
                        userinfo.save()
                    else:
                        return Response({'code': 400, 'msg': "The 'userinfo' does not exist!", 'data': None})
                return Response({'code': 200, 'msg': 'Update userinfo successful!', 'data': None})
            return Response({'code': 400, 'msg': "The 'user' does not exist!", 'data': None})
        except Exception as ex:
            return Response({'code': 500, 'msg': str(ex), 'data': None})
