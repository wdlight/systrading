'use client';

import { useEffect, useState } from 'react';

/**
 * Simple localStorage-backed state hook with SSR guards and JSON serialization.
 * Falls back to provided initial value when storage is unavailable or malformed.
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch {
      // Swallow storage errors silently; callers still receive latest state.
    }
  }, [key, storedValue]);

  return [storedValue, setStoredValue] as const;
}
