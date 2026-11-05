import { useEffect, useRef, useId, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

export default function QrScanner({ onScanSuccess }) {
    const scannerRef = useRef(null);
    const fileInputRef = useRef(null);
    const [errorMsg, setErrorMsg] = useState('');

    const uniqueId = useId().replace(/:/g, "-");
    const containerId = `reader-${uniqueId}`;
    const fileContainerId = `reader-file-${uniqueId}`;

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
                    setErrorMsg('');
                }
            },
            () => {}
        ).catch((err) => {
            console.error("No se pudo iniciar la cámara:", err);
            setErrorMsg("No se pudo acceder a la cámara. Puedes usar la opción de subir imagen.");
        });

        return () => {
            isMounted = false;
            if (scannerRef.current) {
                if (scannerRef.current.isScanning) {
                    scannerRef.current.stop().then(() => {
                        scannerRef.current.clear();
                    }).catch(() => {});
                } else {
                    try {
                        scannerRef.current.clear();
                    } catch (e) {}
                }
            }
        };
    }, [onScanSuccess, containerId]);

    const handleFileUpload = async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const html5QrCodeFile = new Html5Qrcode(fileContainerId);

        try {
            const decodedText = await html5QrCodeFile.scanFile(file, true);
            onScanSuccess(decodedText);
            setErrorMsg('');
        } catch (err) {
            console.error("Error al escanear el archivo QR:", err);
            setErrorMsg("No se pudo detectar un código QR válido en la imagen seleccionada.");
        } finally {
            try {
                await html5QrCodeFile.clear();
            } catch (e) {}
            event.target.value = '';
        }
    };

    return (
        <div className="w-full flex flex-col items-center gap-3">
            <div id={containerId} style={{ width: '100%' }}></div>
            <div id={fileContainerId} style={{ display: 'none' }}></div>

            {errorMsg && (
                <p className="text-red-400 text-sm text-center">{errorMsg}</p>
            )}

            <div className="w-full flex justify-center mt-2">
                <label 
                    htmlFor={`qr-file-input-${uniqueId}`}
                    className="cursor-pointer bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded-lg shadow transition-all flex items-center gap-2 text-sm"
                >
                    <span>📁 Subir imagen de QR</span>
                </label>
                <input 
                    id={`qr-file-input-${uniqueId}`}
                    ref={fileInputRef}
                    type="file" 
                    accept="image/*" 
                    className="hidden" 
                    onChange={handleFileUpload}
                />
            </div>
        </div>
    );
}