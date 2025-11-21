import React, { useEffect, useMemo, useState } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  LayoutDashboard,
  Package,
  Users,
  Map,
  TrendingUp,
  Route as RouteIcon,
  LogOut
} from 'lucide-react';
import Overview from './vendor/Overview';
import Orders from './vendor/Orders';
import Drivers from './vendor/Drivers';
import FleetMap from './vendor/FleetMap';
import Reports from './vendor/Reports';
import RoutePlanner from './vendor/RoutePlanner';
import { drivers as driverApi, orders, vendors } from '@/services/api';

const navItems = [
  { label: 'Overview', path: 'overview', icon: LayoutDashboard },
  { label: 'Orders', path: 'orders', icon: Package },
  { label: 'Drivers', path: 'drivers', icon: Users },
  { label: 'Fleet map', path: 'fleet-map', icon: Map },
  { label: 'Reports', path: 'reports', icon: TrendingUp },
  { label: 'Route planner', path: 'route-planner', icon: RouteIcon }
];

const VendorDashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [vendor, setVendor] = useState(null);
  const [stats, setStats] = useState({ totalOrders: 0, activeDrivers: 0, completedToday: 0 });
  const [driverList, setDriverList] = useState([]);
  const [selectedDriverId, setSelectedDriverId] = useState('');
  const [selectedDriver, setSelectedDriver] = useState(null);

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
      const vendorMatch = vendorRes.data.find((record) => record.user_id === userId);
      if (vendorMatch) {
        setVendor(vendorMatch);
        fetchStats(vendorMatch.id);
        fetchDrivers(vendorMatch.id);
      }
    } catch (error) {
      toast.error('Unable to load vendor profile');
      console.error(error);
    }
  };

  const fetchStats = async (vendorId) => {
    try {
      const [ordersRes, driversRes] = await Promise.all([
        orders.getAll({ vendor_id: vendorId }),
        driverApi.getAll({ vendor_id: vendorId })
      ]);
      const completedToday = ordersRes.data.filter((order) => {
        const createdAt = new Date(order.created_at);
        const today = new Date();
        return order.status === 'delivered' && createdAt.toDateString() === today.toDateString();
      }).length;
      setStats({
        totalOrders: ordersRes.data.length,
        activeDrivers: driversRes.data.filter((driver) => driver.status !== 'offline').length,
        completedToday
      });
    } catch (error) {
      console.error('Error loading stats', error);
    }
  };

  const fetchDrivers = async (vendorId) => {
    try {
      const res = await vendors.getDrivers(vendorId);
      setDriverList(res.data);
    } catch (error) {
      toast.error('Unable to load drivers');
    }
  };

  useEffect(() => {
    const driver = driverList.find((d) => d.id === selectedDriverId);
    setSelectedDriver(driver || null);
  }, [selectedDriverId, driverList]);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const activePath = location.pathname.replace('/vendor/', '') || 'overview';

  const driverStatusBadge = useMemo(() => {
    if (!selectedDriver) return null;
    const variants = {
      available: 'bg-green-100 text-green-800',
      busy: 'bg-orange-100 text-orange-800',
      on_break: 'bg-yellow-100 text-yellow-800',
      offline: 'bg-gray-100 text-gray-800'
    };
    return (
      <Badge className={variants[selectedDriver.status] || 'bg-slate-100 text-slate-900'}>
        {selectedDriver.status?.replace(/_/g, ' ') || 'unknown'}
      </Badge>
    );
  }, [selectedDriver]);

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="vendor-dashboard">
      <aside className="hidden w-64 flex-shrink-0 border-r bg-white/90 backdrop-blur md:flex md:flex-col">
        <div className="border-b px-6 py-5">
          <p className="text-xs uppercase text-muted-foreground">Vendor</p>
          <p className="text-lg font-semibold truncate">{vendor?.business_name || 'Loading...'}</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ label, path, icon: Icon }) => (
            <NavLink
              key={path}
              to={`/vendor/${path}`}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
                  isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                ].join(' ')
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t px-6 py-4">
          <Button variant="outline" className="w-full justify-start" onClick={handleLogout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      </aside>

      <main className="flex-1">
        <header className="sticky top-0 z-10 border-b bg-white/80 backdrop-blur">
          <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm uppercase text-muted-foreground">Vendor console</p>
              <h1 className="text-2xl font-semibold capitalize">{activePath.replace('-', ' ')}</h1>
            </div>
            <div className="flex flex-col gap-2 md:w-80">
              <Select value={selectedDriverId} onValueChange={setSelectedDriverId}>
                <SelectTrigger>
                  <SelectValue placeholder="Quick driver glance" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Select driver</SelectItem>
                  {driverList.map((driver) => (
                    <SelectItem key={driver.id} value={driver.id}>
                      {driver.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedDriver && (
                <Card>
                  <CardContent className="flex items-center justify-between p-3 text-sm">
                    <div>
                      <p className="font-medium">{selectedDriver.full_name}</p>
                      <p className="text-xs text-muted-foreground">{selectedDriver.phone}</p>
                    </div>
                    {driverStatusBadge}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </header>

        <section className="mx-auto max-w-6xl px-6 py-6">
          <Routes>
            <Route index element={<Navigate to="overview" replace />} />
            <Route path="overview" element={<Overview vendor={vendor} stats={stats} />} />
            <Route path="orders" element={<Orders vendorId={vendor?.id} drivers={driverList} />} />
            <Route
              path="drivers"
              element={<Drivers vendorId={vendor?.id} drivers={driverList} refreshDrivers={() => fetchDrivers(vendor?.id)} />}
            />
            <Route path="fleet-map" element={<FleetMap vendorId={vendor?.id} />} />
            <Route path="reports" element={<Reports vendorId={vendor?.id} />} />
            <Route path="route-planner" element={<RoutePlanner />} />
            <Route path="*" element={<Navigate to="overview" replace />} />
          </Routes>
        </section>
      </main>
    </div>
  );
};

export default VendorDashboard;
