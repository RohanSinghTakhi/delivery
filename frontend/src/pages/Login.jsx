import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { auth, vendors, drivers } from '../services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Truck } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  
  // Login State
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  
  // Register State
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    role: 'user'
  });
  
  // Vendor Register State
  const [vendorData, setVendorData] = useState({
    business_name: '',
    email: '',
    phone: '',
    address: '',
    password: ''
  });
  
  // Driver Register State
  const [driverData, setDriverData] = useState({
    full_name: '',
    email: '',
    phone: '',
    vehicle_type: 'bike',
    vehicle_number: '',
    license_number: '',
    password: '',
    vendor_id: ''
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await auth.login(loginData);
      const { access_token, refresh_token, user } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      toast.success('Login successful!');
      
      // Navigate based on role
      if (user.role === 'vendor' || user.role === 'admin') {
        navigate('/vendor/dashboard');
      } else if (user.role === 'driver') {
        navigate('/driver/orders');
      } else {
        navigate('/login');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await auth.register(registerData);
      toast.success('Registration successful! Please login.');
      setActiveTab('login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVendorRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await vendors.register(vendorData);
      toast.success('Vendor registered! Please login.');
      setActiveTab('login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Vendor registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDriverRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await drivers.register(driverData);
      toast.success('Driver registered! Please login.');
      setActiveTab('login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Driver registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <Card className="w-full max-w-md" data-testid="login-card">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-purple-600 p-3 rounded-full">
              <Truck className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center">MedEx Delivery</CardTitle>
          <CardDescription className="text-center">
            B2B Medical Delivery System
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login" data-testid="login-tab">Login</TabsTrigger>
              <TabsTrigger value="register" data-testid="register-tab">Register</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4" data-testid="login-form">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@example.com"
                    value={loginData.email}
                    onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                    required
                    data-testid="login-email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    required
                    data-testid="login-password"
                  />
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="login-submit-btn">
                  {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Logging in...</> : 'Login'}
                </Button>
              </form>
            </TabsContent>
            
            <TabsContent value="register">
              <Tabs defaultValue="user" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="user">User</TabsTrigger>
                  <TabsTrigger value="vendor">Vendor</TabsTrigger>
                  <TabsTrigger value="driver">Driver</TabsTrigger>
                </TabsList>
                
                <TabsContent value="user">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Full Name</Label>
                      <Input
                        value={registerData.full_name}
                        onChange={(e) => setRegisterData({ ...registerData, full_name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={registerData.email}
                        onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input
                        value={registerData.phone}
                        onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Password</Label>
                      <Input
                        type="password"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full" disabled={loading}>
                      {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Registering...</> : 'Register'}
                    </Button>
                  </form>
                </TabsContent>
                
                <TabsContent value="vendor">
                  <form onSubmit={handleVendorRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Business Name</Label>
                      <Input
                        value={vendorData.business_name}
                        onChange={(e) => setVendorData({ ...vendorData, business_name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={vendorData.email}
                        onChange={(e) => setVendorData({ ...vendorData, email: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input
                        value={vendorData.phone}
                        onChange={(e) => setVendorData({ ...vendorData, phone: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Address</Label>
                      <Input
                        value={vendorData.address}
                        onChange={(e) => setVendorData({ ...vendorData, address: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Password</Label>
                      <Input
                        type="password"
                        value={vendorData.password}
                        onChange={(e) => setVendorData({ ...vendorData, password: e.target.value })}
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full" disabled={loading}>
                      {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Registering...</> : 'Register Vendor'}
                    </Button>
                  </form>
                </TabsContent>
                
                <TabsContent value="driver">
                  <form onSubmit={handleDriverRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Full Name</Label>
                      <Input
                        value={driverData.full_name}
                        onChange={(e) => setDriverData({ ...driverData, full_name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={driverData.email}
                        onChange={(e) => setDriverData({ ...driverData, email: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input
                        value={driverData.phone}
                        onChange={(e) => setDriverData({ ...driverData, phone: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Vehicle Type</Label>
                      <Select value={driverData.vehicle_type} onValueChange={(value) => setDriverData({ ...driverData, vehicle_type: value })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="bike">Bike</SelectItem>
                          <SelectItem value="scooter">Scooter</SelectItem>
                          <SelectItem value="car">Car</SelectItem>
                          <SelectItem value="van">Van</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Vehicle Number</Label>
                      <Input
                        value={driverData.vehicle_number}
                        onChange={(e) => setDriverData({ ...driverData, vehicle_number: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>License Number</Label>
                      <Input
                        value={driverData.license_number}
                        onChange={(e) => setDriverData({ ...driverData, license_number: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Vendor ID</Label>
                      <Input
                        value={driverData.vendor_id}
                        onChange={(e) => setDriverData({ ...driverData, vendor_id: e.target.value })}
                        required
                        placeholder="Enter vendor ID"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Password</Label>
                      <Input
                        type="password"
                        value={driverData.password}
                        onChange={(e) => setDriverData({ ...driverData, password: e.target.value })}
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full" disabled={loading}>
                      {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Registering...</> : 'Register Driver'}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;