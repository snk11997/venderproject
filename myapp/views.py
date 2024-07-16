from rest_framework import generics
from rest_framework.response import Response
from .models import Vendor, PurchaseOrder
from .serializers import VendorSerializer, PurchaseOrderSerializer
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.decorators import api_view
from django.db.models import Avg, Count
from .models import PurchaseOrder
from django.db.models import F


@api_view(['GET'])
def vendor_performance(request, vendor_id):
    purchase_orders = PurchaseOrder.objects.filter(vendor_id=vendor_id)
    total_orders = purchase_orders.count()
    if total_orders == 0:
        return Response({'error': 'No purchase orders found for this vendor.'}, status=404)

    # Calculate on-time delivery rate
    on_time_delivery_rate = purchase_orders.filter(status='delivered', delivery_date__lte=timezone.now()).count() / total_orders * 100

    # Calculate average quality rating
    quality_rating_avg = purchase_orders.aggregate(Avg('quality_rating'))['quality_rating__avg']

    # Calculate average response time
    total_response_time = sum((po.acknowledgment_date - po.issue_date).total_seconds() for po in purchase_orders if po.acknowledgment_date)
    average_response_time = total_response_time / total_orders if total_orders != 0 else None

    # Calculate fulfilment rate
    fulfilment_rate = purchase_orders.filter(status='completed').count() / total_orders * 100

    performance_metrics = {
        'on_time_delivery_rate': round(on_time_delivery_rate, 2),
        'quality_rating_avg': round(quality_rating_avg, 2) if quality_rating_avg else None,
        'average_response_time': round(average_response_time / 3600, 2) if average_response_time else None,
        'fulfilment_rate': round(fulfilment_rate, 2),
    }

    return Response(performance_metrics)



class VendorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        self.update_vendor_performance(instance)

    def update_vendor_performance(self, vendor_instance):
        # Calculate performance metrics and update the vendor instance
        purchase_orders = PurchaseOrder.objects.filter(vendor=vendor_instance)
        total_orders = purchase_orders.count()
        if total_orders == 0:
            return
        on_time_delivery_rate = purchase_orders.filter(status='delivered', delivery_date__lte=timezone.now()).count() / total_orders * 100
        quality_rating_avg = purchase_orders.aggregate(Avg('quality_rating'))['quality_rating__avg']
        average_response_time = purchase_orders.aggregate(Avg('acknowledgment_date' - 'issue_date'))['acknowledgment_date__avg']
        fulfilment_rate = purchase_orders.filter(status='completed').count() / total_orders * 100

        vendor_instance.on_time_delivery_rate = round(on_time_delivery_rate, 2)
        vendor_instance.quality_rating_avg = round(quality_rating_avg, 2) if quality_rating_avg else 0
        vendor_instance.average_response_time = round(average_response_time.total_seconds() / 3600, 2) if average_response_time else 0
        vendor_instance.fulfilment_rate = round(fulfilment_rate, 2)
        vendor_instance.save()

class VendorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

class PurchaseOrderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    
        
class PurchaseOrderListCreateAPIView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.status == 'completed':
            self.update_vendor_performance(instance.vendor)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status == 'completed':
            self.update_vendor_performance(instance.vendor)

    def update_vendor_performance(self, vendor_instance):
        # Calculate performance metrics and update the vendor instance
        purchase_orders = PurchaseOrder.objects.filter(vendor=vendor_instance, status='completed')
        total_completed_orders = purchase_orders.count()
        if total_completed_orders == 0:
            return
        on_time_delivery_rate = purchase_orders.filter(delivery_date__lte=timezone.now()).count() / total_completed_orders * 100
        quality_rating_avg = purchase_orders.aggregate(Avg('quality_rating'))['quality_rating__avg']
        vendor_instance.on_time_delivery_rate = round(on_time_delivery_rate, 2)
        vendor_instance.quality_rating_avg = round(quality_rating_avg, 2) if quality_rating_avg else 0
        vendor_instance.save()


class PurchaseOrderAcknowledgeAPIView(generics.UpdateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    def perform_update(self, serializer):
        instance = serializer.save(acknowledgment_date=timezone.now())
        self.update_vendor_average_response_time(instance.vendor)

    def update_vendor_average_response_time(self, vendor_instance):
        # Calculate average response time and update the vendor instance
        purchase_orders = PurchaseOrder.objects.filter(vendor=vendor_instance, acknowledgment_date__isnull=False)
        total_acknowledged_orders = purchase_orders.count()
        if total_acknowledged_orders == 0:
            return
        
        total_response_time = sum((po.acknowledgment_date - po.issue_date).total_seconds() for po in purchase_orders)
        average_response_time = total_response_time / total_acknowledged_orders
        vendor_instance.average_response_time = round(average_response_time / 3600, 2)
        vendor_instance.save()


@receiver(post_save, sender=PurchaseOrder)
def update_vendor_performance(sender, instance, **kwargs):
    if instance.status == 'completed':
        vendor = instance.vendor
        purchase_orders = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
        total_completed_orders = purchase_orders.count()
        if total_completed_orders == 0:
            return
        on_time_delivery_rate = purchase_orders.filter(delivery_date__lte=timezone.now()).count() / total_completed_orders * 100
        quality_rating_avg = purchase_orders.aggregate(Avg('quality_rating'))['quality_rating__avg']
        vendor.on_time_delivery_rate = round(on_time_delivery_rate, 2)
        vendor.quality_rating_avg = round(quality_rating_avg, 2) if quality_rating_avg else 0
        vendor.save()


@receiver(post_save, sender=PurchaseOrder)
def update_vendor_average_response_time(sender, instance, **kwargs):
    if instance.acknowledgment_date:
        vendor = instance.vendor
        purchase_orders = PurchaseOrder.objects.filter(vendor=vendor, acknowledgment_date__isnull=False)
        total_acknowledged_orders = purchase_orders.count()
        if total_acknowledged_orders == 0:
            return
        average_response_time = purchase_orders.aggregate(avg_response_time=Avg(F('acknowledgment_date') - F('issue_date')))['avg_response_time']
        vendor.average_response_time = round(average_response_time.total_seconds() / 3600, 2) if average_response_time else 0
        vendor.save()


class VendorPerformanceAPIView(generics.ListAPIView):
    serializer_class = VendorSerializer

    def get_queryset(self):
        vendors = Vendor.objects.all()
        performance_data = []
        
        for vendor in vendors:
            performance_metrics = self.calculate_performance_metrics(vendor)
            performance_data.append({
                'vendor': vendor,
                'performance_metrics': performance_metrics
            })
        
        return performance_data

    def calculate_performance_metrics(self, vendor):
        purchase_orders = PurchaseOrder.objects.filter(vendor=vendor)
        total_orders = purchase_orders.count()
        
        if total_orders == 0:
            return None

        on_time_delivery_rate = purchase_orders.filter(status='delivered', delivery_date__lte=timezone.now()).count() / total_orders * 100
        quality_rating = purchase_orders.aggregate(Avg('quality_rating'))['quality_rating__avg']
        response_time = purchase_orders.aggregate(Avg('acknowledgment_date' - 'issue_date'))['acknowledgment_date__avg']
        fulfilment_rate = purchase_orders.filter(status='completed').count() / total_orders * 100

        performance_metrics = {
            'on_time_delivery_rate': round(on_time_delivery_rate, 2),
            'quality_rating': round(quality_rating, 2) if quality_rating else None,
            'response_time': round(response_time.total_seconds() / 3600, 2) if response_time else None,
            'fulfilment_rate': round(fulfilment_rate, 2),
        }

        return performance_metrics