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
from waverider_common import (MeshtasticDetector, SignalGenerator, compute_fft_db, SDRDevice, 
                             RTLSDR_AVAILABLE, AudioDemodulator, FMDemodulator, AMDemodulator, 
                             SSBDemodulator, AUDIO_AVAILABLE, WaterfallSettings, BandPlan)


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
        
        # Audio processing
        self.audio_enabled = False
        self.modulation_mode = 'FM'
        self.audio_rate = 48000
        self.demodulator = FMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
        
        # Waterfall settings
        self.waterfall_settings = WaterfallSettings()
        
        # Initialize components
        self.signal_source = SignalGenerator(self.sample_rate, self.center_freq)
        self.meshtastic_detector = MeshtasticDetector()
        self.sdr_device = SDRDevice()
        self.use_real_sdr = False
        self.waterfall_data = np.zeros((self.waterfall_height, self.fft_size))
        
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
            sdr_devices = self.sdr_device.detect_devices() if RTLSDR_AVAILABLE else []
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
                'rtlsdr_available': RTLSDR_AVAILABLE
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
        
        @self.socketio.on('set_band')
        def handle_set_band(data):
            """Set frequency band from band plan"""
            band_name = data.get('band', '')
            band_info = BandPlan.get_band_info(band_name)
            
            if band_info:
                # Set center frequency
                center_freq_mhz = band_info['center'] / 1e6
                self.center_freq = band_info['center']
                self.signal_source.center_freq = self.center_freq
                
                # Update SDR device if connected
                if self.use_real_sdr and self.sdr_device.is_connected:
                    self.sdr_device.set_center_freq(self.center_freq)
                
                # Set recommended modulation mode
                recommended_mode = band_info.get('mode', 'FM')
                if recommended_mode in ['FM', 'AM', 'USB', 'LSB']:
                    self.modulation_mode = recommended_mode
                    
                    # Create appropriate demodulator
                    if recommended_mode == 'FM':
                        self.demodulator = FMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
                    elif recommended_mode == 'AM':
                        self.demodulator = AMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
                    elif recommended_mode == 'USB':
                        self.demodulator = SSBDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate, mode='USB')
                    elif recommended_mode == 'LSB':
                        self.demodulator = SSBDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate, mode='LSB')
                elif recommended_mode == 'WFM':
                    self.modulation_mode = 'FM'
                    self.demodulator = FMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
                
                # Notify client
                desc = band_info.get('description', band_name)
                freq_range = f"{band_info['start']/1e6:.3f} - {band_info['end']/1e6:.3f} MHz"
                emit('status', {'message': f'{desc} | {freq_range} | Mode: {recommended_mode}'})
                emit('band_changed', {
                    'frequency': center_freq_mhz,
                    'modulation': self.modulation_mode,
                    'description': desc
                })
                
                if self.audio_enabled:
                    emit('audio_status', {'message': f'Audio: Ready ({self.modulation_mode})', 'color': 'blue'})
            
        @self.socketio.on('get_bands')
        def handle_get_bands():
            """Get list of all bands"""
            bands = BandPlan.get_all_bands()
            emit('bands_list', {'bands': bands})
            
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
        
        @self.socketio.on('set_modulation')
        def handle_set_modulation(data):
            """Set modulation mode"""
            mode = data.get('mode', 'FM')
            self.modulation_mode = mode
            
            # Create appropriate demodulator
            if mode == 'FM':
                self.demodulator = FMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
            elif mode == 'AM':
                self.demodulator = AMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
            elif mode == 'USB':
                self.demodulator = SSBDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate, mode='USB')
            elif mode == 'LSB':
                self.demodulator = SSBDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate, mode='LSB')
            
            emit('status', {'message': f'Modulation set to {mode}'})
            if self.audio_enabled:
                emit('audio_status', {'message': f'Audio: Ready ({mode})', 'color': 'blue'})
        
        @self.socketio.on('set_audio_enable')
        def handle_set_audio_enable(data):
            """Enable/disable audio output"""
            self.audio_enabled = data.get('enabled', False)
            
            if self.audio_enabled:
                emit('audio_status', {'message': f'Audio: Ready ({self.modulation_mode})', 'color': 'blue'})
                emit('status', {'message': 'Audio output enabled'})
            else:
                emit('audio_status', {'message': 'Audio: Disabled', 'color': 'gray'})
                emit('status', {'message': 'Audio output disabled'})
        
        @self.socketio.on('set_squelch')
        def handle_set_squelch(data):
            """Set squelch threshold"""
            threshold = float(data.get('threshold', -50))
            self.demodulator.set_squelch(threshold)
            emit('status', {'message': f'Squelch: {threshold} dB'})
        
        @self.socketio.on('set_rf_gain')
        def handle_set_rf_gain(data):
            """Set RF gain"""
            gain = float(data.get('gain', 40))
            if self.use_real_sdr and self.sdr_device.is_connected:
                self.sdr_device.set_gain(gain / 10.0)
            emit('status', {'message': f'RF Gain: {gain} dB'})
        
        @self.socketio.on('set_colormap')
        def handle_set_colormap(data):
            """Set waterfall colormap"""
            colormap = data.get('colormap', 'viridis')
            self.waterfall_settings.set_colormap(colormap)
            emit('status', {'message': f'Colormap: {colormap}'})
        
        @self.socketio.on('set_waterfall_range')
        def handle_set_waterfall_range(data):
            """Set waterfall display range"""
            min_db = float(data.get('min_db', -80))
            max_db = float(data.get('max_db', 0))
            self.waterfall_settings.set_range(min_db, max_db)
            emit('status', {'message': f'Range: {min_db} to {max_db} dB'})
        
        @self.socketio.on('set_peak_hold')
        def handle_set_peak_hold(data):
            """Enable/disable peak hold"""
            enabled = data.get('enabled', False)
            self.waterfall_settings.peak_hold = enabled
            if not enabled:
                self.waterfall_settings.peak_buffer = None
            emit('status', {'message': f'Peak hold {"enabled" if enabled else "disabled"}'})
        
        @self.socketio.on('scan_sdr_devices')
        def handle_scan_sdr_devices():
            """Scan for SDR devices"""
            if not RTLSDR_AVAILABLE:
                emit('sdr_devices', {
                    'devices': [],
                    'error': 'RTL-SDR library not installed. Install with: pip install pyrtlsdr'
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
                
                # Compute FFT and convert to dB
                fft_db = compute_fft_db(samples, self.fft_size)
                
                # Apply waterfall processing (contrast, brightness, peak hold)
                fft_processed = self.waterfall_settings.apply_processing(fft_db)
                
                # Update waterfall
                self.waterfall_data = np.roll(self.waterfall_data, 1, axis=0)
                self.waterfall_data[0, :] = fft_processed
                
                # Generate and send image
                img_data = self.generate_waterfall_image()
                img_b64 = base64.b64encode(img_data).decode('utf-8')
                
                self.socketio.emit('waterfall_update', {'image': img_b64})
                
                # Process audio if enabled
                if self.audio_enabled:
                    # Detect if signal is strong enough
                    if self.demodulator.detect_signal(samples):
                        # Demodulate to audio
                        audio_samples = self.demodulator.demodulate(samples)
                        
                        # Convert to bytes and encode as base64
                        audio_bytes = audio_samples.tobytes()
                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        
                        # Send audio data to client
                        self.socketio.emit('audio_data', {
                            'data': audio_b64,
                            'sample_rate': self.audio_rate,
                            'channels': 1
                        })
                        
                        # Update audio status
                        self.socketio.emit('audio_status', {
                            'message': f'Audio: Playing ({self.modulation_mode})',
                            'color': 'green'
                        })
                    else:
                        # No strong signal detected
                        self.socketio.emit('audio_status', {
                            'message': f'Audio: Waiting for signal ({self.modulation_mode})',
                            'color': 'orange'
                        })
                
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
            
            # Create waterfall plot with current settings
            im = ax.imshow(self.waterfall_data, 
                          aspect='auto', 
                          cmap=self.waterfall_settings.colormap,
                          interpolation='bilinear',
                          vmin=self.waterfall_settings.min_db, 
                          vmax=self.waterfall_settings.max_db,
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
