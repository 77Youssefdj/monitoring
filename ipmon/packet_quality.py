from flask import Blueprint, render_template
from ipmon.database import PollHistory

packet_quality_bp = Blueprint('packet_quality', __name__)

@packet_quality_bp.route('/packet_quality')
def packet_quality():
    # Calculate metrics
    packet_loss, latency, jitter = calculate_packet_quality()

    # Debug print statements
    print(f"Packet Loss: {packet_loss}%")
    print(f"Latency: {latency} ms")
    print(f"Jitter: {jitter} ms")

    return render_template('packetQuality.html', packet_loss=packet_loss, latency=latency, jitter=jitter)
def calculate_packet_quality():
    # Fetch poll history data
    poll_data = PollHistory.query.all()

    # Debug print to verify data
    print(f"Raw Poll Data: {poll_data}")

    if not poll_data:
        return 0, 0, 0  # Return zero values if no data

    total_packets = len(poll_data)
    print(f"Total Packets: {total_packets}")

    # Count 'lost' packets
    lost_packets = sum(1 for p in poll_data if p.poll_status.lower() == 'down')
    print(f"Lost Packets: {lost_packets}")

    # Assuming no latency data for now, set latency to zero
    total_latency = 0
    latency = total_latency / total_packets if total_packets else 0
    print(f"Total Latency: {total_latency}")

    # Calculate jitter
    total_jitter = calculate_jitter(poll_data)
    print(f"Total Jitter: {total_jitter}")

    packet_loss = (lost_packets / total_packets) * 100 if total_packets else 0
    jitter = total_jitter / (total_packets - 1) if total_packets > 1 else 0

    return round(packet_loss, 2), round(latency, 2), round(jitter, 2)

def calculate_jitter(poll_data):
    # Jitter calculation assumes we have numeric latencies; this needs to be adapted based on actual latency data
    # For simplicity, let's assume jitter as the difference between consecutive status changes
    # In this case, latency data is missing so jitter calculation may not be meaningful
    latencies = []  # Populate this if you have latency data

    if len(latencies) < 2:
        return 0

    jitter = sum(abs(latencies[i] - latencies[i - 1]) for i in range(1, len(latencies)))
    return jitter / (len(latencies) - 1) if len(latencies) > 1 else 0
