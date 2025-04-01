import time

class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        method = request.method
        path = request.path

        print(f"\n IP: {ip} ")

        response = self.get_response(request)

        duration = time.time() - start_time

        print(f"  --> Response time: {duration:.4f}s")

        return response