"""
Performance tests.
"""
import os
import glob
import time
import pytest
from pyzxing import DecodeError


class TestPerformance:
    """Test performance characteristics."""
    
    def test_single_file_performance(self, barcode_reader, sample_barcode_files):
        """Test single file decoding performance."""
        # Test with a simple barcode
        start_time = time.time()
        result = barcode_reader.decode(sample_barcode_files['qrcode'])
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 10.0  # 10 seconds max
        assert isinstance(result, list)
    
    def test_multiple_files_performance(self, barcode_reader, sample_barcode_files):
        """Test multiple files decoding performance."""
        start_time = time.time()
        results = barcode_reader.decode('src/resources/*.png')
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 30.0  # 30 seconds max
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_memory_usage(self, barcode_reader, sample_barcode_files):
        """Test memory usage is reasonable."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss
        
        # Decode multiple files
        for _ in range(5):
            barcode_reader.decode(sample_barcode_files['qrcode'])
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        
        # Memory increase should be reasonable (< 50MB)
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50 * 1024 * 1024  # 50MB
    
    def test_parallel_processing_matches_sequential(self, barcode_reader):
        """Parallel processing must preserve sequential decoding results."""
        # Compare the same set of inputs in both branches.
        png_files = glob.glob('src/resources/*.png')
        
        assert len(png_files) >= 2, "parallel test requires at least two PNG fixtures"
        
        # Test sequential processing (simulate)
        sequential_results = []
        for file_path in png_files:
            sequential_results.extend(barcode_reader.decode(file_path))

        parallel_results = barcode_reader.decode('src/resources/*.png')

        sequential_values = {item.get('parsed') for item in sequential_results}
        parallel_values = {item.get('parsed') for item in parallel_results}
        assert parallel_values == sequential_values
    
    def test_large_file_handling(self, barcode_reader, temp_dir):
        """Test handling of large image files."""
        # Create a large dummy image file
        large_file = os.path.join(temp_dir, 'large.png')
        
        # Create a minimal PNG that's large in size
        with open(large_file, 'wb') as f:
            # Write PNG header
            f.write(b'\x89PNG\r\n\x1a\n')
            # Write large IDAT chunk
            f.write(b'\x00\x00\x00\rIHDR')
            f.write(b'\x00\x00\xFF\xFF\x00\x00\xFF\xFF')  # Large dimensions
            f.write(b'\x08\x02\x00\x00\x00')
            # Write large amount of data
            large_data = b'\x00' * (1024 * 1024)  # 1MB of data
            f.write(large_data)
        
        # Invalid image data must fail clearly instead of looking like no barcode.
        start_time = time.time()
        with pytest.raises(DecodeError):
            barcode_reader.decode(large_file)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 30.0  # 30 seconds max
    
    def test_concurrent_access(self, barcode_reader, sample_barcode_files):
        """Test concurrent access to BarCodeReader."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker(file_path):
            try:
                result = barcode_reader.decode(file_path)
                results_queue.put(('success', result))
            except Exception as e:
                results_queue.put(('error', str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            file_path = sample_barcode_files['qrcode']
            thread = threading.Thread(target=worker, args=(file_path,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        error_count = 0
        
        while not results_queue.empty():
            status, result = results_queue.get()
            if status == 'success':
                success_count += 1
            else:
                error_count += 1
        
        # All operations should succeed
        assert error_count == 0
        assert success_count == 3
