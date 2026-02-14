'use client';

import { useReportWebVitals } from 'next/web-vitals';

export function WebPerformance() {
  useReportWebVitals((metric) => {
    // En un entorno real, enviaríamos esto a un servicio como Google Analytics, Vercel Analytics o un endpoint propio
    console.log('Web Vital:', metric.name, metric.value, metric.label);
    
    // Ejemplo de envío a un endpoint (simulado)
    /*
    const body = JSON.stringify(metric);
    const url = '/api/vitals';
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, body);
    } else {
      fetch(url, { body, method: 'POST', keepalive: true });
    }
    */
  });

  return null;
}
