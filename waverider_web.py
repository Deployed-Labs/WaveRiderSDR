"""
WaveRiderSDR Web Interface - Cross-Platform Web Version
Works on desktop computers and mobile phones via web browser
"""

import os
import sys
import json
import base64
import io
import threading
import time
import numpy as np
from flask import Flask, render_template, jsonify, Response
from flask_socketio import SocketIO, emit
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# Import common utilities
from waverider_common import (MeshtasticDetector, SignalGenerator, compute_fft_db, 
                               SDRDevice, RTLSDR_AVAILABLE, HACKRF_AVAILABLE,
                               Demodulator, MorseDecoder)


class WaveRiderWebApp:
    """Web-based WaveRider SDR application"""
    
    def __init__(self):
        self.app = Flask(__name__)
        # Generate a random secret key for session security
        import secrets
        self.app.config['SECRET_KEY'] = secrets.token_hex(32)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Signal processing parameters
        self.sample_rate = 2.4e6
        self.center_freq = 100e6
        self.fft_size = 1024
        self.waterfall_height = 100
        self.update_interval = 0.05  # 50ms
        self.running = False
        
        # Initialize components
        self.signal_source = SignalGenerator(self.sample_rate, self.center_freq)
        self.meshtastic_detector = MeshtasticDetector()
        self.sdr_device = SDRDevice()
        self.use_real_sdr = False
        self.waterfall_data = np.zeros((self.waterfall_height, self.fft_size))
        
        # Initialize demodulator and Morse decoder
        self.demodulator = Demodulator(self.sample_rate)
        self.morse_decoder = MorseDecoder(self.sample_rate)
        self.modulation_mode = 'None'
        self.morse_mode_enabled = False
        self.morse_text = ""
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get current status"""
            devices = self.meshtastic_detector.detect_devices()
            sdr_devices = self.sdr_device.detect_devices() if RTLSDR_AVAILABLE or HACKRF_AVAILABLE else []
            return jsonify({
                'running': self.running,
                'sample_rate': self.sample_rate,
                'center_freq': self.center_freq,
                'fft_size': self.fft_size,
                'meshtastic_detected': len(devices) > 0,
                'devices': [{'device': d.device, 'description': d.description} 
                           for d in devices] if devices else [],
                'sdr_devices': sdr_devices,
                'sdr_connected': self.sdr_device.is_connected,
                'use_real_sdr': self.use_real_sdr,
                'rtlsdr_available': RTLSDR_AVAILABLE,
                'hackrf_available': HACKRF_AVAILABLE,
                'modulation_mode': self.modulation_mode,
                'morse_enabled': self.morse_mode_enabled,
                'morse_text': self.morse_text
            })
        
        @self.app.route('/api/waterfall_image')
        def get_waterfall_image():
            """Generate and return waterfall image"""
            img_data = self.generate_waterfall_image()
            return Response(img_data, mimetype='image/png')
    
    def setup_socketio_events(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            emit('status', {'message': 'Connected to WaveRider SDR'})
            
        @self.socketio.on('start')
        def handle_start():
            """Start signal acquisition"""
            if not self.running:
                self.running = True
                threading.Thread(target=self.update_loop, daemon=True).start()
                emit('status', {'message': 'Started'})
            else:
                emit('status', {'message': 'Already running'})
            
        @self.socketio.on('stop')
        def handle_stop():
            """Stop signal acquisition"""
            self.running = False
            emit('status', {'message': 'Stopped'})
            
        @self.socketio.on('set_frequency')
        def handle_set_frequency(data):
            """Set center frequency"""
            freq = float(data.get('frequency', 100))
            self.center_freq = freq * 1e6
            self.signal_source.center_freq = self.center_freq
            
            # Update SDR device if connected
            if self.use_real_sdr and self.sdr_device.is_connected:
                self.sdr_device.set_center_freq(self.center_freq)
            
            emit('status', {'message': f'Frequency set to {freq} MHz'})
            
        @self.socketio.on('set_sample_rate')
        def handle_set_sample_rate(data):
            """Set sample rate"""
            rate_str = data.get('rate', '2.4 MHz')
            rate_map = {
                '2.4 MHz': 2.4e6,
                '2.048 MHz': 2.048e6,
                '1.024 MHz': 1.024e6
            }
            self.sample_rate = rate_map.get(rate_str, 2.4e6)
            self.signal_source.sample_rate = self.sample_rate
            
            # Update SDR device if connected
            if self.use_real_sdr and self.sdr_device.is_connected:
                self.sdr_device.set_sample_rate(self.sample_rate)
            
            emit('status', {'message': f'Sample rate set to {rate_str}'})
            
        @self.socketio.on('set_fft_size')
        def handle_set_fft_size(data):
            """Set FFT size"""
            size = int(data.get('size', 1024))
            self.fft_size = size
            self.waterfall_data = np.zeros((self.waterfall_height, self.fft_size))
            emit('status', {'message': f'FFT size set to {size}'})
        
        @self.socketio.on('scan_sdr_devices')
        def handle_scan_sdr_devices():
            """Scan for SDR devices"""
            if not RTLSDR_AVAILABLE and not HACKRF_AVAILABLE:
                emit('sdr_devices', {
                    'devices': [],
                    'error': 'No SDR libraries installed. Install RTL-SDR with: pip install pyrtlsdr or HackRF via SoapySDR'
                })
                return
            
            devices = self.sdr_device.detect_devices()
            emit('sdr_devices', {'devices': devices, 'error': None})
        
        @self.socketio.on('connect_sdr_device')
        def handle_connect_sdr_device(data):
            """Connect to an SDR device"""
            device_index = data.get('device_index', 0)
            device_type = data.get('device_type', 'RTL-SDR')
            
            # Disconnect from any previous device
            if self.sdr_device.is_connected:
                self.sdr_device.disconnect()
            
            # Connect to the new device
            if self.sdr_device.connect(device_index, device_type):
                self.use_real_sdr = True
                self.sdr_device.set_sample_rate(self.sample_rate)
                self.sdr_device.set_center_freq(self.center_freq)
                emit('status', {'message': f'Connected to {device_type}'})
            else:
                self.use_real_sdr = False
                emit('status', {'message': f'Failed to connect to {device_type}'})
        
        @self.socketio.on('disconnect_sdr_device')
        def handle_disconnect_sdr_device():
            """Disconnect from SDR device"""
            if self.sdr_device.is_connected:
                self.sdr_device.disconnect()
            self.use_real_sdr = False
            emit('status', {'message': 'SDR device disconnected'})
        
        @self.socketio.on('set_modulation')
        def handle_set_modulation(data):
            """Set modulation mode"""
            mode = data.get('mode', 'None')
            self.modulation_mode = mode
            self.demodulator = Demodulator(self.sample_rate)  # Reset demodulator
            emit('status', {'message': f'Modulation set to {mode}'})
        
        @self.socketio.on('toggle_morse')
        def handle_toggle_morse(data):
            """Toggle Morse decoder"""
            enabled = data.get('enabled', False)
            self.morse_mode_enabled = enabled
            
            if enabled:
                self.morse_decoder.reset()
                self.morse_text = ""
                # Automatically set to CW mode
                if self.modulation_mode != 'CW':
                    self.modulation_mode = 'CW'
                    self.demodulator = Demodulator(self.sample_rate)
                emit('status', {'message': 'Morse decoder enabled'})
            else:
                emit('status', {'message': 'Morse decoder disabled'})
    
    def update_loop(self):
        """Main update loop for signal processing"""
        while self.running:
            try:
                # Get samples from real SDR or simulated source
                if self.use_real_sdr and self.sdr_device.is_connected:
                    samples = self.sdr_device.read_samples(self.fft_size)
                    if samples is None:
                        # Error reading from SDR, fall back to simulated
                        samples = self.signal_source.generate_samples(self.fft_size)
                else:
                    # Generate simulated samples
                    samples = self.signal_source.generate_samples(self.fft_size)
                
                # Apply demodulation if Morse mode is enabled (CW detection)
                if self.morse_mode_enabled and self.modulation_mode == 'CW' and samples is not None:
                    demod_signal = self.demodulator.demodulate_cw(samples)
                    new_text = self.morse_decoder.process_samples(demod_signal)
                    if new_text:
                        self.morse_text += new_text
                        # Emit Morse update
                        self.socketio.emit('morse_update', {'text': new_text})
                
                # Compute FFT and convert to dB
                fft_db = compute_fft_db(samples, self.fft_size)
                
                # Update waterfall
                self.waterfall_data = np.roll(self.waterfall_data, 1, axis=0)
                self.waterfall_data[0, :] = fft_db
                
                # Generate and send image
                img_data = self.generate_waterfall_image()
                img_b64 = base64.b64encode(img_data).decode('utf-8')
                
                self.socketio.emit('waterfall_update', {'image': img_b64})
                
                # Sleep for update interval
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error in update loop: {e}")
                break
    
    def generate_waterfall_image(self):
        """Generate waterfall visualization as image"""
        try:
            fig = Figure(figsize=(10, 6), dpi=80)
            ax = fig.add_subplot(111)
            
            # Create waterfall plot
            im = ax.imshow(self.waterfall_data, 
                          aspect='auto', 
                          cmap='viridis',
                          interpolation='bilinear',
                          vmin=-80, vmax=0,
                          extent=[0, self.fft_size, self.waterfall_height, 0])
            
            # Set labels
            freq_start = (self.center_freq - self.sample_rate / 2) / 1e6
            freq_end = (self.center_freq + self.sample_rate / 2) / 1e6
            
            ax.set_xlabel('Frequency (MHz)')
            ax.set_ylabel('Time')
            ax.set_title('Waterfall Display (Spectrogram)')
            
            # Set x-axis ticks
            num_ticks = 5
            tick_positions = np.linspace(0, self.fft_size, num_ticks)
            tick_labels = [f'{freq:.2f}' for freq in np.linspace(freq_start, freq_end, num_ticks)]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels)
            
            fig.colorbar(im, ax=ax, label='Power (dB)')
            fig.tight_layout()
            
            # Convert to image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            img_data = buf.getvalue()
            plt.close(fig)
            
            return img_data
            
        except Exception as e:
            print(f"Error generating waterfall image: {e}")
            # Return a blank image
            fig = Figure(figsize=(10, 6))
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            return buf.getvalue()
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the web application
        
        Args:
            host: Host to bind to. Use '0.0.0.0' for all interfaces (mobile access),
                  or '127.0.0.1' for localhost only (more secure)
            port: Port to listen on
            debug: Enable debug mode
        """
        print(f"Starting WaveRider SDR Web Interface on http://{host}:{port}")
        
        if host == '0.0.0.0':
            print("\n⚠️  SECURITY NOTICE:")
            print("   Binding to 0.0.0.0 allows connections from any device on your network.")
            print("   This is required for mobile device access but less secure.")
            print("   For localhost-only access, use: app.run(host='127.0.0.1')")
            print("   Consider using firewall rules to restrict access to trusted devices.\n")
        
        print("Access from any device (computer or phone) using a web browser")
        self.socketio.run(self.app, host=host, port=port, debug=debug)


def main():
    """Main entry point"""
    app = WaveRiderWebApp()
    # Start the web server
    # Use 0.0.0.0 to allow connections from any device on the network
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
