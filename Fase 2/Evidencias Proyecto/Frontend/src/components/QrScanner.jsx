import { useEffect, useRef, useId, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

export default function QrScanner({ onScanSuccess }) {
    const scannerRef = useRef(null);
    const alEscanearRef = useRef(onScanSuccess);
    const [errorMsg, setErrorMsg] = useState('');

    const uniqueId = useId().replace(/:/g, "-");
    const containerId = `reader-${uniqueId}`;
    const fileContainerId = `reader-file-${uniqueId}`;
    const fileInputId = `qr-file-input-${uniqueId}`;

    // La función que llega por props cambia en cada render del padre.
    // Se guarda en una ref para no reiniciar la cámara cada vez que eso ocurre.
    useEffect(() => {
        alEscanearRef.current = onScanSuccess;
    }, [onScanSuccess]);

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
                    alEscanearRef.current(decodedText);
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
    }, [containerId]);

    const handleFileUpload = async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const html5QrCodeFile = new Html5Qrcode(fileContainerId);

        try {
            const decodedText = await html5QrCodeFile.scanFile(file, true);
            alEscanearRef.current(decodedText);
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
        <div className="qr-scanner">
            <div id={containerId} style={{ width: '100%' }}></div>
            <div id={fileContainerId} style={{ display: 'none' }}></div>

            {errorMsg && <p className="qr-scanner-error">{errorMsg}</p>}

            <label htmlFor={fileInputId} className="boton boton-secundario qr-scanner-subir">
                Subir imagen de QR
            </label>
            <input
                id={fileInputId}
                type="file"
                accept="image/*"
                className="qr-scanner-oculto"
                onChange={handleFileUpload}
            />
        </div>
    );
}