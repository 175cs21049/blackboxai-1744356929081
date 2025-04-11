// DOM Elements
const userName = document.getElementById('userName');
const employeeId = document.getElementById('employeeId');
const checkInBtn = document.getElementById('checkInBtn');
const checkOutBtn = document.getElementById('checkOutBtn');
const checkInTime = document.getElementById('checkInTime');
const checkOutTime = document.getElementById('checkOutTime');
const workingHours = document.getElementById('workingHours');
const attendanceHistory = document.getElementById('attendanceHistory');
const logoutBtn = document.getElementById('logoutBtn');

// Load user data and attendance history when page loads
document.addEventListener('DOMContentLoaded', async () => {
    await loadUserData();
    await loadTodayStatus();
    await loadAttendanceHistory();
});

// Load user data
async function loadUserData() {
    try {
        const response = await fetch('/api/user');
        const data = await response.json();
        
        if (data.status === 'success') {
            userName.textContent = data.user.fullName;
            employeeId.textContent = `Employee ID: ${data.user.employeeId}`;
        } else {
            showError('Failed to load user data');
        }
    } catch (err) {
        console.error('Error loading user data:', err);
        showError('Error loading user data');
    }
}

// Load today's attendance status
async function loadTodayStatus() {
    try {
        const response = await fetch('/api/attendance/today');
        const data = await response.json();
        
        if (data.status === 'success') {
            updateTodayStatus(data.attendance);
        } else {
            showError('Failed to load today\'s attendance status');
        }
    } catch (err) {
        console.error('Error loading today\'s status:', err);
        showError('Error loading today\'s status');
    }
}

// Update today's status display
function updateTodayStatus(attendance) {
    if (attendance.checkIn) {
        checkInTime.textContent = new Date(attendance.checkIn).toLocaleTimeString();
        checkInBtn.disabled = true;
    }
    
    if (attendance.checkOut) {
        checkOutTime.textContent = new Date(attendance.checkOut).toLocaleTimeString();
        checkOutBtn.disabled = true;
        
        // Calculate working hours
        const checkInDate = new Date(attendance.checkIn);
        const checkOutDate = new Date(attendance.checkOut);
        const hours = ((checkOutDate - checkInDate) / (1000 * 60 * 60)).toFixed(2);
        workingHours.textContent = `${hours} hours`;
    }
}

// Load attendance history
async function loadAttendanceHistory() {
    try {
        const response = await fetch('/api/attendance/history');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayAttendanceHistory(data.history);
        } else {
            showError('Failed to load attendance history');
        }
    } catch (err) {
        console.error('Error loading attendance history:', err);
        showError('Error loading attendance history');
    }
}

// Display attendance history in table
function displayAttendanceHistory(history) {
    attendanceHistory.innerHTML = '';
    
    history.forEach(record => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        const date = new Date(record.date).toLocaleDateString();
        const checkIn = record.checkIn ? new Date(record.checkIn).toLocaleTimeString() : '-';
        const checkOut = record.checkOut ? new Date(record.checkOut).toLocaleTimeString() : '-';
        const hours = record.checkIn && record.checkOut ? 
            ((new Date(record.checkOut) - new Date(record.checkIn)) / (1000 * 60 * 60)).toFixed(2) + ' hours' : 
            '-';
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${date}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${checkIn}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${checkOut}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${hours}</td>
        `;
        
        attendanceHistory.appendChild(row);
    });
}

// Handle Check In
checkInBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/attendance/check-in', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('Check-in successful!');
            await loadTodayStatus();
            await loadAttendanceHistory();
        } else {
            showError(data.message || 'Check-in failed');
        }
    } catch (err) {
        console.error('Error during check-in:', err);
        showError('Error during check-in');
    }
});

// Handle Check Out
checkOutBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/attendance/check-out', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('Check-out successful!');
            await loadTodayStatus();
            await loadAttendanceHistory();
        } else {
            showError(data.message || 'Check-out failed');
        }
    } catch (err) {
        console.error('Error during check-out:', err);
        showError('Error during check-out');
    }
});

// Handle Logout
logoutBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            window.location.href = '/';
        } else {
            showError('Logout failed');
        }
    } catch (err) {
        console.error('Error during logout:', err);
        showError('Error during logout');
    }
});

// Utility functions for showing success/error messages
function showSuccess(message) {
    // You can implement a toast notification here
    alert(message);
}

function showError(message) {
    // You can implement a toast notification here
    alert(message);
}
