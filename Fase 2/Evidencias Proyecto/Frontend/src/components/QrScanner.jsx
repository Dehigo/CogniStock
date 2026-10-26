import { useEffect, useRef, useId } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

export default function QrScanner({ onScanSuccess }) {
    const scannerRef = useRef(null);
    // Genera un ID único y seguro para evitar colisiones en el DOM durante el StrictMode de React
    const uniqueId = useId().replace(/:/g, "-");
    const containerId = `reader-${uniqueId}`;

    useEffect(() => {
        let isMounted = true;
        const html5QrCode = new Html5Qrcode(containerId);
        scannerRef.current = html5QrCode;

        const config = { fps: 10, qrbox: { width: 250, height: 250 } };

        html5QrCode.start(
            { facingMode: "environment" }, 
            config,
            (decodedText) => {
                if (isMounted) {
                    onScanSuccess(decodedText);
                }
            },
            (errorMessage) => {
            }
        ).catch((err) => {
            console.error("No se pudo iniciar la cámara:", err);
        });

        return () => {
            isMounted = false;
            if (scannerRef.current) {
                if (scannerRef.current.isScanning) {
                    scannerRef.current.stop().then(() => {
                        scannerRef.current.clear();
                    }).catch(() => {
                    });
                } else {
                    try {
                        scannerRef.current.clear();
                    } catch (e) {
                    }
                }
            }
        };
    }, [onScanSuccess, containerId]);

    return (
        <div style={{ width: '100%', maxWidth: '500px', margin: '0 auto' }}>
            <div id={containerId} style={{ width: '100%' }}></div>
        </div>
    );
}