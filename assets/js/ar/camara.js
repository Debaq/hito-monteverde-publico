// Abre la cámara trasera en el <video>. Si falla, dice por qué y cómo se arregla: un
// mensaje genérico no ayuda a nadie parado frente a un cartel.

const $ = id => document.getElementById(id);

const POR_QUE = {
  NotAllowedError: 'Rechazaste el permiso. Se reactiva en el candado de la barra de direcciones.',
  NotFoundError: 'No se encontró la cámara trasera de este aparato.',
  NotReadableError: 'Otra aplicación está usando la cámara. Cierra Meet, Zoom o la app de cámara.',
  OverconstrainedError: 'La cámara no admite la resolución que pide la detección.',
};

function fallar(titulo, texto) {
  $('fallaTitulo').textContent = titulo;
  $('fallaTexto').textContent = texto;
  $('falla').classList.add('on');
}

/**
 * `alAbrir()`: la cámara ya da cuadros. `registrar(evento, datos)`: la analítica, que
 * anota si abrió o por qué no, para saber cuánta gente se queda afuera.
 */
export function montarCamara(video, { alAbrir, registrar }) {
  let flujo = null;

  async function encender() {
    if (!isSecureContext) {
      fallar('Conexión no segura',
        `Chrome bloquea la cámara en ${location.origin}\n` +
        'porque no es un origen seguro.\n\n' +
        'En este computador: entra por http://localhost:8080\n' +
        'Por wifi: hace falta HTTPS, o agregar el origen en\n' +
        'chrome://flags/#unsafely-treat-insecure-origin-as-secure');
      return;
    }
    try {
      const camaras = (await navigator.mediaDevices.enumerateDevices())
        .filter(d => d.kind === 'videoinput');
      if (!camaras.length) {
        registrar('ar_camara', { detalle: 'sin_camara' });
        fallar('Sin cámara', 'No hay ninguna cámara conectada.');
        return;
      }
      flujo?.getTracks().forEach(t => t.stop());
      flujo = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: 'environment' },
                 width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      video.srcObject = flujo;
      await video.play();
      $('falla').classList.remove('on');
      alAbrir();
      registrar('ar_camara', { detalle: 'ok' });
    } catch (e) {
      registrar('ar_camara', { detalle: e.name });
      fallar('No se pudo abrir la cámara', (POR_QUE[e.name] || e.message) + ` (${e.name})`);
    }
  }

  $('reintentar').addEventListener('click', () => { $('falla').classList.remove('on'); encender(); });
  encender();                     // sin cartel de por medio: la cámara es la página
}
