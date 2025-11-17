import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LogOut, MapPin, Package, CheckCircle, Navigation } from 'lucide-react';
import { orders, drivers } from '../services/api';
import { getCurrentLocation, watchPosition, clearWatch } from '../utils/maps';

const DriverApp = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [driverData, setDriverData] = useState(null);
  const [driverOrders, setDriverOrders] = useState([]);
  const [isOnline, setIsOnline] = useState(false);
  const [locationWatchId, setLocationWatchId] = useState(null);
  const [currentLocation, setCurrentLocation] = useState(null);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const userData = JSON.parse(userStr);
      setUser(userData);
      loadDriverData(userData.id);
    }

    return () => {
      if (locationWatchId) {
        clearWatch(locationWatchId);
      }
    };
  }, []);

  const loadDriverData = async (userId) => {
    try {
      const driversRes = await drivers.getAll();
      const driver = driversRes.data.find(d => d.user_id === userId);
      if (driver) {
        setDriverData(driver);
        setIsOnline(driver.status !== 'offline');
        loadDriverOrders(driver.id);
      }
    } catch (error) {
      console.error('Error loading driver data:', error);
    }
  };

  const loadDriverOrders = async (driverId) => {
    try {
      const ordersRes = await orders.getAll({ driver_id: driverId });
      const activeOrders = ordersRes.data.filter(o => 
        ['driver_assigned', 'picked_up', 'out_for_delivery'].includes(o.status)
      );
      setDriverOrders(activeOrders);
    } catch (error) {
      console.error('Error loading orders:', error);
    }
  };

  const toggleOnlineStatus = async () => {
    if (!driverData) return;

    try {
      if (isOnline) {
        // Go offline
        await drivers.updateStatus(driverData.id, 'offline');
        if (locationWatchId) {
          clearWatch(locationWatchId);
          setLocationWatchId(null);
        }
        setIsOnline(false);
        toast.success('You are now offline');
      } else {
        // Go online and start location tracking
        await drivers.updateStatus(driverData.id, 'available');
        startLocationTracking();
        setIsOnline(true);
        toast.success('You are now online');
      }
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const startLocationTracking = async () => {
    try {
      const location = await getCurrentLocation();
      setCurrentLocation(location);
      
      // Update initial location
      if (driverData) {
        await drivers.updateLocation(driverData.id, location.lat, location.lng);
      }

      // Start watching location
      const watchId = watchPosition(
        async (position) => {
          setCurrentLocation(position);
          if (driverData) {
            await drivers.updateLocation(driverData.id, position.lat, position.lng);
          }
        },
        (error) => {
          console.error('Location error:', error);
          toast.error('Failed to get location');
        }
      );
      
      setLocationWatchId(watchId);
    } catch (error) {
      toast.error('Failed to access location. Please enable location services.');
    }
  };

  const handleOrderAction = async (orderId, newStatus) => {
    try {
      await orders.updateStatus(orderId, newStatus);
      toast.success(`Order ${newStatus}`);
      if (driverData) {
        loadDriverOrders(driverData.id);
      }
    } catch (error) {
      toast.error('Failed to update order status');
    }
  };

  const handleLogout = () => {
    if (locationWatchId) {
      clearWatch(locationWatchId);
    }
    localStorage.clear();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const getStatusColor = (status) => {
    const colors = {
      available: 'bg-green-500',
      busy: 'bg-yellow-500',
      offline: 'bg-gray-500',
      on_break: 'bg-blue-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  return (
    <div className="min-h-screen bg-gray-50" data-testid="driver-app">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Driver App</h1>
              <p className="text-sm text-gray-600">{driverData?.full_name || 'Loading...'}</p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={toggleOnlineStatus}
                variant={isOnline ? "destructive" : "default"}
                size="sm"
                data-testid="toggle-status-btn"
              >
                <div className={`h-2 w-2 rounded-full ${getStatusColor(isOnline ? 'available' : 'offline')} mr-2`} />
                {isOnline ? 'Go Offline' : 'Go Online'}
              </Button>
              <Button onClick={handleLogout} variant="outline" size="sm" data-testid="logout-btn">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Current Location */}
        {currentLocation && (
          <Card className="mb-6" data-testid="current-location-card">
            <CardHeader>
              <CardTitle className="text-sm flex items-center">
                <MapPin className="h-4 w-4 mr-2 text-blue-600" />
                Current Location
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Lat: {currentLocation.lat.toFixed(6)}, Lng: {currentLocation.lng.toFixed(6)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Accuracy: {currentLocation.accuracy?.toFixed(0)}m | Speed: {(currentLocation.speed || 0).toFixed(1)} km/h
              </p>
            </CardContent>
          </Card>
        )}

        {/* Active Orders */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-4">Active Deliveries</h2>
          {driverOrders.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Package className="h-12 w-12 mx-auto text-gray-400 mb-3" />
                <p className="text-gray-600">No active deliveries</p>
                <p className="text-sm text-gray-500 mt-1">
                  {isOnline ? 'Waiting for assignments...' : 'Go online to receive orders'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {driverOrders.map((order) => (
                <Card key={order.id} data-testid={`order-card-${order.order_number}`}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base">{order.order_number}</CardTitle>
                        <p className="text-sm text-gray-600 mt-1">{order.customer_name}</p>
                      </div>
                      <Badge variant="outline">{order.status.replace('_', ' ')}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-700">Delivery Address</p>
                        <p className="text-sm text-gray-600">{order.delivery_address}</p>
                      </div>
                      
                      <div className="flex gap-2 flex-wrap">
                        {order.status === 'driver_assigned' && (
                          <Button
                            size="sm"
                            onClick={() => handleOrderAction(order.id, 'picked_up')}
                            data-testid={`pickup-btn-${order.order_number}`}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Mark Picked Up
                          </Button>
                        )}
                        {order.status === 'picked_up' && (
                          <Button
                            size="sm"
                            onClick={() => handleOrderAction(order.id, 'out_for_delivery')}
                            data-testid={`out-for-delivery-btn-${order.order_number}`}
                          >
                            <Navigation className="h-4 w-4 mr-1" />
                            Out for Delivery
                          </Button>
                        )}
                        {order.status === 'out_for_delivery' && (
                          <Button
                            size="sm"
                            onClick={() => handleOrderAction(order.id, 'delivered')}
                            data-testid={`delivered-btn-${order.order_number}`}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Mark Delivered
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Info Note */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> When online, your location is automatically shared every few seconds.
            Full implementation includes Google Maps navigation, proof of delivery photo capture,
            signature collection, and real-time communication with vendor dashboard.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DriverApp;