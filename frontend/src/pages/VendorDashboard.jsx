import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LogOut, Package, Users, TrendingUp, Map } from 'lucide-react';
import { orders, drivers, vendors, reports } from '../services/api';

const VendorDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [vendorData, setVendorData] = useState(null);
  const [stats, setStats] = useState({ totalOrders: 0, activeDrivers: 0, completedToday: 0 });

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const userData = JSON.parse(userStr);
      setUser(userData);
      loadVendorData(userData.id);
    }
  }, []);

  const loadVendorData = async (userId) => {
    try {
      const vendorRes = await vendors.getAll();
      const vendor = vendorRes.data.find(v => v.user_id === userId);
      if (vendor) {
        setVendorData(vendor);
        loadStats(vendor.id);
      }
    } catch (error) {
      console.error('Error loading vendor data:', error);
    }
  };

  const loadStats = async (vendorId) => {
    try {
      const [ordersRes, driversRes] = await Promise.all([
        orders.getAll({ vendor_id: vendorId }),
        drivers.getAll({ vendor_id: vendorId })
      ]);
      
      const completedToday = ordersRes.data.filter(o => {
        const createdAt = new Date(o.created_at);
        const today = new Date();
        return o.status === 'delivered' && 
               createdAt.toDateString() === today.toDateString();
      }).length;

      setStats({
        totalOrders: ordersRes.data.length,
        activeDrivers: driversRes.data.filter(d => d.status !== 'offline').length,
        completedToday
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  return (
    <div className="min-h-screen bg-gray-50" data-testid="vendor-dashboard">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Vendor Dashboard</h1>
              <p className="text-sm text-gray-600">{vendorData?.business_name || 'Loading...'}</p>
            </div>
            <Button onClick={handleLogout} variant="outline" data-testid="logout-btn">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card data-testid="total-orders-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Orders</CardTitle>
              <Package className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalOrders}</div>
            </CardContent>
          </Card>

          <Card data-testid="active-drivers-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Active Drivers</CardTitle>
              <Users className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.activeDrivers}</div>
            </CardContent>
          </Card>

          <Card data-testid="completed-today-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Completed Today</CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.completedToday}</div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link to="/vendor/orders">
              <Button className="w-full" data-testid="view-orders-btn">
                <Package className="mr-2 h-4 w-4" />
                View Orders
              </Button>
            </Link>
            <Link to="/vendor/drivers">
              <Button className="w-full" data-testid="manage-drivers-btn">
                <Users className="mr-2 h-4 w-4" />
                Manage Drivers
              </Button>
            </Link>
            <Link to="/vendor/fleet-map">
              <Button className="w-full" data-testid="fleet-map-btn">
                <Map className="mr-2 h-4 w-4" />
                Fleet Map
              </Button>
            </Link>
            <Link to="/vendor/reports">
              <Button className="w-full" data-testid="reports-btn">
                <TrendingUp className="mr-2 h-4 w-4" />
                Reports
              </Button>
            </Link>
          </div>
        </div>

        {/* Info Note */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> This is the main vendor dashboard. Full order management, driver tracking,
            and reporting features are available through the quick action buttons above. The complete
            implementation includes real-time fleet tracking with Google Maps, driver assignment workflows,
            and comprehensive reporting.
          </p>
        </div>
      </div>
    </div>
  );
};

export default VendorDashboard;