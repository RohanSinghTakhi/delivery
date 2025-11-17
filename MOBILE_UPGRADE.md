# Mobile Upgrade Guide

## Overview

This guide explains how to convert the current responsive Driver Web UI into native mobile apps using Expo (React Native). The web UI is already built mobile-first and can be ported with minimal changes.

## Current State: Mobile-First Web App

The Driver Web UI (`/app/frontend/src/pages/DriverApp.jsx`) is:
- ✅ Fully responsive (mobile-first design)
- ✅ Touch-optimized controls
- ✅ Uses browser geolocation API
- ✅ Works on mobile browsers
- ✅ Can be added to home screen (PWA-ready)

### Limitations of Web App:
- ❌ No background location tracking
- ❌ No push notifications
- ❌ Battery optimization issues
- ❌ Limited offline capabilities
- ❌ Not on App Stores

## Option 1: Progressive Web App (PWA)

### Pros
- Minimal additional development
- Single codebase
- Instant updates
- No app store approval

### Cons
- No background geolocation
- Limited iOS support
- Not discoverable in app stores

### Implementation Steps

1. **Add Service Worker**
```javascript
// public/service-worker.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('medex-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/js/main.js',
        '/static/css/main.css'
      ]);
    })
  );
});
```

2. **Update manifest.json**
```json
{
  "name": "MedEx Driver",
  "short_name": "MedEx",
  "start_url": "/driver",
  "display": "standalone",
  "theme_color": "#667eea",
  "background_color": "#ffffff",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

3. **Register Service Worker**
```javascript
// index.js
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js');
}
```

## Option 2: Expo (React Native) - **RECOMMENDED**

### Why Expo?
- Native mobile experience
- Background location tracking
- Push notifications
- Better performance
- App Store distribution
- Shared React codebase

### Requirements

**Emergent Platform**:
- ⚠️ Expo mobile development requires **paid subscription**
- Emergent will provide:
  - Expo project generation
  - Mobile build service
  - App store deployment assistance

**Development Prerequisites**:
- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- iOS: Mac with Xcode (for iOS builds)
- Android: Android Studio (for Android builds)
- Expo Go app (for testing)

### Architecture Comparison

| Component | Web App | React Native |
|-----------|---------|-------------|
| UI Framework | React + HTML/CSS | React Native components |
| Styling | Tailwind CSS | StyleSheet / styled-components |
| Navigation | React Router | React Navigation |
| HTTP | Axios | Axios (same) |
| WebSocket | socket.io-client | socket.io-client (same) |
| Maps | Google Maps JS API | react-native-maps |
| Geolocation | Browser API | expo-location |
| Storage | localStorage | AsyncStorage |
| Camera | HTML input | expo-camera |

## Step-by-Step Migration

### Phase 1: Project Setup

1. **Create Expo Project**
```bash
npx create-expo-app medex-driver --template blank-typescript
cd medex-driver
```

2. **Install Dependencies**
```bash
npx expo install \
  expo-location \
  expo-camera \
  expo-notifications \
  react-native-maps \
  @react-navigation/native \
  @react-navigation/stack \
  axios \
  socket.io-client \
  @react-native-async-storage/async-storage
```

3. **Configure app.json**
```json
{
  "expo": {
    "name": "MedEx Driver",
    "slug": "medex-driver",
    "version": "1.0.0",
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.medex.driver",
      "infoPlist": {
        "NSLocationAlwaysAndWhenInUseUsageDescription": "We need your location to track deliveries",
        "NSLocationWhenInUseUsageDescription": "We need your location to track deliveries",
        "NSCameraUsageDescription": "We need camera access for proof of delivery"
      }
    },
    "android": {
      "package": "com.medex.driver",
      "permissions": [
        "ACCESS_FINE_LOCATION",
        "ACCESS_COARSE_LOCATION",
        "ACCESS_BACKGROUND_LOCATION",
        "CAMERA"
      ]
    }
  }
}
```

### Phase 2: Code Migration

#### 1. Convert Components

**Before (Web - DriverApp.jsx)**:
```jsx
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const DriverApp = () => {
  return (
    <div className="container">
      <Card>
        <h1 className="text-2xl">Driver App</h1>
        <Button onClick={handleAction}>Action</Button>
      </Card>
    </div>
  );
};
```

**After (React Native - DriverApp.tsx)**:
```tsx
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Card } from './components/Card';

const DriverApp = () => {
  return (
    <View style={styles.container}>
      <Card>
        <Text style={styles.title}>Driver App</Text>
        <TouchableOpacity style={styles.button} onPress={handleAction}>
          <Text style={styles.buttonText}>Action</Text>
        </TouchableOpacity>
      </Card>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold' },
  button: { padding: 12, backgroundColor: '#667eea', borderRadius: 8 },
  buttonText: { color: '#fff', textAlign: 'center' }
});
```

#### 2. Geolocation Migration

**Before (Web)**:
```javascript
import { getCurrentLocation, watchPosition } from '../utils/maps';

const location = await getCurrentLocation();
const watchId = watchPosition(onUpdate, onError);
```

**After (React Native)**:
```typescript
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';

const LOCATION_TASK = 'background-location-task';

// Foreground location
const location = await Location.getCurrentPositionAsync({
  accuracy: Location.Accuracy.High
});

// Background location tracking
TaskManager.defineTask(LOCATION_TASK, async ({ data, error }) => {
  if (error) {
    console.error(error);
    return;
  }
  if (data) {
    const { locations } = data;
    // Send location to backend
    await sendLocationUpdate(locations[0]);
  }
});

await Location.startLocationUpdatesAsync(LOCATION_TASK, {
  accuracy: Location.Accuracy.High,
  timeInterval: 5000,
  distanceInterval: 10,
  foregroundService: {
    notificationTitle: 'MedEx Driver',
    notificationBody: 'Tracking your delivery location'
  }
});
```

#### 3. Maps Integration

**Before (Web)**:
```jsx
import { createMap, createMarker } from '../utils/maps';

const map = await createMap('map-container', options);
const marker = createMarker(map, position, options);
```

**After (React Native)**:
```tsx
import MapView, { Marker } from 'react-native-maps';

<MapView
  style={styles.map}
  initialRegion={{
    latitude: 40.7128,
    longitude: -74.0060,
    latitudeDelta: 0.0922,
    longitudeDelta: 0.0421
  }}
>
  <Marker
    coordinate={{ latitude: 40.7128, longitude: -74.0060 }}
    title="Delivery Location"
  />
</MapView>
```

#### 4. Camera/File Upload

**Before (Web)**:
```jsx
<input type="file" accept="image/*" onChange={handleFileSelect} />
```

**After (React Native)**:
```tsx
import * as ImagePicker from 'expo-image-picker';
import { Camera } from 'expo-camera';

const takePhoto = async () => {
  const permission = await Camera.requestCameraPermissionsAsync();
  if (!permission.granted) return;
  
  const result = await ImagePicker.launchCameraAsync({
    mediaTypes: ImagePicker.MediaTypeOptions.Images,
    quality: 0.8
  });
  
  if (!result.canceled) {
    uploadProof(result.assets[0].uri);
  }
};
```

#### 5. Storage Migration

**Before (Web)**:
```javascript
localStorage.setItem('access_token', token);
const token = localStorage.getItem('access_token');
```

**After (React Native)**:
```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

await AsyncStorage.setItem('access_token', token);
const token = await AsyncStorage.getItem('access_token');
```

### Phase 3: Push Notifications

```typescript
import * as Notifications from 'expo-notifications';

// Register for push notifications
const { status } = await Notifications.requestPermissionsAsync();
if (status !== 'granted') return;

const token = await Notifications.getExpoPushTokenAsync();
// Send token to backend

// Handle incoming notifications
Notifications.addNotificationReceivedListener(notification => {
  console.log('Notification received:', notification);
});

Notifications.addNotificationResponseReceivedListener(response => {
  // Handle notification tap
  const { orderId } = response.notification.request.content.data;
  navigation.navigate('OrderDetail', { orderId });
});
```

### Phase 4: Testing

1. **Development Testing**
```bash
npx expo start
# Scan QR code with Expo Go app
```

2. **iOS Simulator**
```bash
npx expo start --ios
```

3. **Android Emulator**
```bash
npx expo start --android
```

### Phase 5: Build & Deploy

#### Expo Application Services (EAS)

1. **Install EAS CLI**
```bash
npm install -g eas-cli
eas login
```

2. **Configure EAS**
```bash
eas build:configure
```

3. **Build for iOS**
```bash
eas build --platform ios
# Generates .ipa file for App Store
```

4. **Build for Android**
```bash
eas build --platform android
# Generates .aab file for Play Store
```

5. **Submit to Stores**
```bash
eas submit --platform ios
eas submit --platform android
```

## Cost Breakdown

### Emergent Paid Subscription
- Expo project generation
- Build service access
- Deployment assistance
- Contact Emergent for pricing

### Additional Costs
- Apple Developer Program: $99/year (required for iOS)
- Google Play Console: $25 one-time (required for Android)
- Expo EAS Build: $29/month (for cloud builds)
- Push Notification Service: Free (Expo)

## Migration Checklist

### Pre-Migration
- [ ] Confirm Emergent paid subscription
- [ ] Set up Apple Developer account
- [ ] Set up Google Play Console account
- [ ] Install development tools

### Migration
- [ ] Create Expo project
- [ ] Port UI components
- [ ] Migrate API services (already compatible)
- [ ] Implement background geolocation
- [ ] Add camera functionality
- [ ] Implement push notifications
- [ ] Migrate storage to AsyncStorage
- [ ] Test on iOS and Android

### Post-Migration
- [ ] Build production apps
- [ ] Test on real devices
- [ ] Submit to App Stores
- [ ] Set up analytics
- [ ] Monitor crash reports

## Alternative: Capacitor

If you prefer to keep the web codebase:

```bash
npm install @capacitor/core @capacitor/cli
npx cap init
npx cap add ios
npx cap add android

# Add plugins
npm install @capacitor/geolocation
npm install @capacitor/camera
npm install @capacitor/push-notifications

# Build
npm run build
npx cap copy
npx cap open ios
npx cap open android
```

**Pros**: Keep existing React web code
**Cons**: More complex debugging, less native feel

## Recommended Approach

1. **Start with PWA** for immediate mobile support
2. **Upgrade to Expo** when:
   - You need background location tracking
   - You want app store distribution
   - Budget allows for paid subscription
3. **Contact Emergent** to enable mobile features

## Support

For Emergent-specific mobile features:
- Contact Emergent support
- Provide your subscription details
- Request Expo project generation

---

**Note**: The current web implementation is fully functional on mobile browsers. Native apps are recommended for production use with background capabilities.