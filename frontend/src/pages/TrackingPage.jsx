import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPin, Package, Clock, Truck } from 'lucide-react';
import { tracking } from '../services/api';

const TrackingPage = () => {
  const { token } = useParams();
  const [orderData, setOrderData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTrackingData();
    // Poll for updates every 10 seconds
    const interval = setInterval(loadTrackingData, 10000);
    return () => clearInterval(interval);
  }, [token]);

  const loadTrackingData = async () => {
    try {
      const response = await tracking.getByToken(token);
      setOrderData(response.data);
      setLoading(false);
    } catch (err) {
      setError('Invalid tracking token or order not found');
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      accepted: 'bg-blue-100 text-blue-800',
      driver_assigned: 'bg-purple-100 text-purple-800',
      picked_up: 'bg-indigo-100 text-indigo-800',
      out_for_delivery: 'bg-orange-100 text-orange-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusSteps = () => {
    const steps = [
      { key: 'pending', label: 'Order Placed' },
      { key: 'accepted', label: 'Accepted' },
      { key: 'driver_assigned', label: 'Driver Assigned' },
      { key: 'picked_up', label: 'Picked Up' },
      { key: 'out_for_delivery', label: 'Out for Delivery' },
      { key: 'delivered', label: 'Delivered' }
    ];

    const currentIndex = steps.findIndex(s => s.key === orderData?.order?.status);
    
    return steps.map((step, index) => ({
      ...step,
      completed: index <= currentIndex,
      active: index === currentIndex
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Card className="w-full max-w-md">
          <CardContent className="py-12 text-center">
            <Package className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-900 mb-2">Tracking Error</p>
            <p className="text-sm text-gray-600">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }} data-testid="tracking-page">
      <div className="max-w-2xl mx-auto">
        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-2xl mb-1" data-testid="order-number">
                  {orderData?.order?.order_number}
                </CardTitle>
                <p className="text-sm text-gray-600">{orderData?.order?.customer_name}</p>
              </div>
              <Badge className={getStatusColor(orderData?.order?.status)} data-testid="order-status">
                {orderData?.order?.status?.replace('_', ' ')}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Delivery Address */}
              <div className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-purple-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-700">Delivery Address</p>
                  <p className="text-sm text-gray-600">{orderData?.order?.delivery_address}</p>
                </div>
              </div>

              {/* ETA */}
              {orderData?.eta_minutes && (
                <div className="flex items-start gap-3">
                  <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-700">Estimated Time</p>
                    <p className="text-sm text-gray-600">{orderData.eta_minutes} minutes</p>
                  </div>
                </div>
              )}

              {/* Driver Location */}
              {orderData?.driver_location && (
                <div className="flex items-start gap-3">
                  <Truck className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-700">Driver Location</p>
                    <p className="text-sm text-gray-600">
                      Lat: {orderData.driver_location.latitude?.toFixed(6)}, 
                      Lng: {orderData.driver_location.longitude?.toFixed(6)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Last updated: {new Date(orderData.driver_location.last_update).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Progress Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Delivery Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {getStatusSteps().map((step, index) => (
                <div key={step.key} className="flex items-center gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                      step.completed ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-500'
                    }`}>
                      {step.completed ? '✓' : index + 1}
                    </div>
                    {index < getStatusSteps().length - 1 && (
                      <div className={`h-12 w-0.5 ${
                        step.completed ? 'bg-purple-600' : 'bg-gray-200'
                      }`} />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`font-medium ${
                      step.active ? 'text-purple-600' : step.completed ? 'text-gray-900' : 'text-gray-500'
                    }`}>
                      {step.label}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Info Note */}
        <div className="mt-6 bg-white rounded-lg p-4">
          <p className="text-sm text-gray-600">
            <strong>Note:</strong> This page updates automatically every 10 seconds. In full implementation,
            this includes real-time WebSocket updates, live map with driver marker, and route visualization.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TrackingPage;