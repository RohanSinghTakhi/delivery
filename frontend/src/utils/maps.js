import { Loader } from '@googlemaps/js-api-loader';

const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || 'YOUR_GOOGLE_MAPS_API_KEY_HERE';

let mapLoader = null;
let googleMaps = null;

export const initGoogleMaps = async () => {
  if (googleMaps) return googleMaps;

  if (!mapLoader) {
    mapLoader = new Loader({
      apiKey: GOOGLE_MAPS_API_KEY,
      version: 'weekly',
      libraries: ['places', 'geometry']
    });
  }

  try {
    googleMaps = await mapLoader.load();
    return googleMaps;
  } catch (error) {
    console.error('Error loading Google Maps:', error);
    throw error;
  }
};

export const createMap = async (elementId, options) => {
  await initGoogleMaps();
  const mapElement = document.getElementById(elementId);
  
  const defaultOptions = {
    zoom: 12,
    center: { lat: 40.7128, lng: -74.0060 }, // Default to NYC
    ...options
  };

  return new window.google.maps.Map(mapElement, defaultOptions);
};

export const createMarker = (map, position, options = {}) => {
  const defaultOptions = {
    position,
    map,
    ...options
  };

  return new window.google.maps.Marker(defaultOptions);
};

export const getCurrentLocation = () => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
      },
      (error) => reject(error),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  });
};

export const watchPosition = (onUpdate, onError) => {
  if (!navigator.geolocation) {
    onError(new Error('Geolocation not supported'));
    return null;
  }

  return navigator.geolocation.watchPosition(
    (position) => {
      onUpdate({
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        speed: position.coords.speed || 0,
        heading: position.coords.heading || 0,
        accuracy: position.coords.accuracy
      });
    },
    onError,
    { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
  );
};

export const clearWatch = (watchId) => {
  if (watchId && navigator.geolocation) {
    navigator.geolocation.clearWatch(watchId);
  }
};