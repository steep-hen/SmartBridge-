"""Goal Progress Dashboard Templates.

Provides:
- Dashboard view for goal progress visualization
- Progress cards component
- Goal highlights summary
- Time remaining tracker
"""

# This is a Flask template that would be rendered server-side
# File: templates/dashboard/goals_dashboard.html

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Goal Progress Dashboard - SmartBridge</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .dashboard-header {
            color: white;
            margin-bottom: 40px;
            text-align: center;
        }
        
        .dashboard-header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .dashboard-header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        /* HIGHLIGHTS SECTION */
        .highlights-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .highlight-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .highlight-card:hover {
            transform: translateY(-5px);
        }
        
        .highlight-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 15px 0;
        }
        
        .highlight-card .label {
            font-size: 0.95em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .highlight-card.on-track {
            border-left: 5px solid #4caf50;
        }
        
        .highlight-card.behind {
            border-left: 5px solid #ff9800;
        }
        
        .highlight-card.completed {
            border-left: 5px solid #2196f3;
        }
        
        /* GOALS GRID */
        .goals-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .goal-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .goal-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.25);
        }
        
        .goal-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .goal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .goal-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        .goal-type {
            display: inline-block;
            background: #f0f0f0;
            color: #666;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        
        .goal-status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-on-track {
            background: #c8e6c9;
            color: #2e7d32;
        }
        
        .status-in-progress {
            background: #bbdefb;
            color: #1565c0;
        }
        
        .status-just-started {
            background: #ffe0b2;
            color: #e65100;
        }
        
        .status-complete {
            background: #c8e6c9;
            color: #2e7d32;
        }
        
        .goal-amounts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
        }
        
        .amount-box {
            text-align: center;
        }
        
        .amount-label {
            font-size: 0.85em;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .amount-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        /* PROGRESS BAR */
        .progress-section {
            margin-bottom: 20px;
        }
        
        .progress-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        
        .progress-label-name {
            color: #666;
            font-weight: 600;
        }
        
        .progress-label-percent {
            color: #667eea;
            font-weight: bold;
        }
        
        .progress-bar {
            width: 100%;
            height: 10px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
            transition: width 0.5s ease;
        }
        
        /* TIME & DATES */
        .time-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
            padding: 12px;
            background: #f9f9f9;
            border-radius: 8px;
        }
        
        .time-box {
            text-align: center;
        }
        
        .time-label {
            font-size: 0.8em;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .time-value {
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
        }
        
        /* MONTHLY CONTRIBUTION */
        .contribution-box {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            padding: 12px;
            background: #f0f7ff;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 3px solid #2196f3;
        }
        
        .contribution-current {
            text-align: center;
        }
        
        .contribution-required {
            text-align: center;
        }
        
        .contribution-label {
            font-size: 0.8em;
            color: #0d47a1;
            text-transform: uppercase;
            margin-bottom: 5px;
            font-weight: 600;
        }
        
        .contribution-value {
            font-size: 1.1em;
            font-weight: bold;
            color: #0d47a1;
        }
        
        /* RECOMMENDATION */
        .recommendation-box {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 12px;
            border-radius: 6px;
            margin-top: 15px;
        }
        
        .recommendation-title {
            font-size: 0.85em;
            color: #e65100;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .recommendation-text {
            font-size: 0.9em;
            color: #e65100;
            line-height: 1.4;
        }
        
        .recommendation-box.urgent {
            background: #ffebee;
            border-left-color: #f44336;
        }
        
        .recommendation-box.urgent .recommendation-title {
            color: #c62828;
        }
        
        .recommendation-box.urgent .recommendation-text {
            color: #c62828;
        }
        
        .recommendation-box.positive {
            background: #e8f5e9;
            border-left-color: #4caf50;
        }
        
        .recommendation-box.positive .recommendation-title {
            color: #2e7d32;
        }
        
        .recommendation-box.positive .recommendation-text {
            color: #2e7d32;
        }
        
        /* PRIORITY GOALS */
        .priority-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
            margin-bottom: 40px;
        }
        
        .priority-section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        
        .priority-goals {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .priority-goal {
            padding: 15px;
            border-radius: 10px;
            background: #f5f5f5;
        }
        
        .priority-goal.highest {
            border-left: 4px solid #f44336;
        }
        
        .priority-goal.closest {
            border-left: 4px solid #4caf50;
        }
        
        .priority-goal-title {
            font-size: 0.9em;
            color: #999;
            text-transform: uppercase;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .priority-goal-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        
        .priority-goal-progress {
            font-size: 0.95em;
            color: #666;
        }
        
        /* RESPONSIVE */
        @media (max-width: 768px) {
            .dashboard-header h1 {
                font-size: 1.8em;
            }
            
            .goals-grid {
                grid-template-columns: 1fr;
            }
            
            .priority-goals {
                grid-template-columns: 1fr;
            }
            
            .goal-amounts {
                grid-template-columns: 1fr;
            }
        }
        
        /* ANIMATIONS */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .goal-card {
            animation: fadeIn 0.6s ease-out;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="dashboard-header">
            <h1>🎯 Goal Progress Dashboard</h1>
            <p>Track your financial goals and monitor progress towards your dreams</p>
        </div>
        
        <!-- HIGHLIGHTS -->
        <div class="highlights-section" id="highlightsSection">
            <div class="highlight-card">
                <div class="label">Total Goals</div>
                <div class="value" id="totalGoals">0</div>
            </div>
            <div class="highlight-card">
                <div class="label">Completed</div>
                <div class="value" id="completedGoals">0</div>
            </div>
            <div class="highlight-card">
                <div class="label">On Track</div>
                <div class="value" id="onTrackGoals">0</div>
            </div>
            <div class="highlight-card">
                <div class="label">Behind Schedule</div>
                <div class="value" id="behindGoals">0</div>
            </div>
            <div class="highlight-card">
                <div class="label">Average Progress</div>
                <div class="value" id="avgProgress">0%</div>
            </div>
        </div>
        
        <!-- PRIORITY SECTION -->
        <div class="priority-section" id="prioritySection" style="display: none;">
            <h2>⚡ Priority Focus</h2>
            <div class="priority-goals">
                <div class="priority-goal highest">
                    <div class="priority-goal-title">Highest Priority</div>
                    <div class="priority-goal-name" id="highestPriorityName">-</div>
                    <div class="priority-goal-progress" id="highestPriorityProgress">-</div>
                </div>
                <div class="priority-goal closest">
                    <div class="priority-goal-title">Closest to Completion</div>
                    <div class="priority-goal-name" id="closestName">-</div>
                    <div class="priority-goal-progress" id="closestProgress">-</div>
                </div>
            </div>
        </div>
        
        <!-- GOALS GRID -->
        <div class="goals-grid" id="goalsGrid">
            <!-- Goals will be populated here -->
        </div>
    </div>
    
    <script>
        // Sample data - in real app, this would be fetched from API
        const sampleGoals = [
            {
                goal_id: "goal-001",
                goal_name: "Home Purchase",
                goal_type: "INVESTMENT",
                target_amount: 5000000,
                current_amount: 1500000,
                monthly_contribution: 50000,
                expected_completion_date: "2030-05",
                months_remaining: 42,
                years_remaining: 3.5,
                on_track: false,
                progress_percent: 30.0,
                progress_status: "In Progress",
                monthly_required: 157437.86,
                remaining_amount: 3500000,
                priority_recommendation: "Increase contribution to ₹157,438/month to stay on track"
            },
            {
                goal_id: "goal-002",
                goal_name: "Child Education",
                goal_type: "EDUCATION",
                target_amount: 1500000,
                current_amount: 1200000,
                monthly_contribution: 8000,
                expected_completion_date: "2026-06",
                months_remaining: 5,
                years_remaining: 0.4,
                on_track: true,
                progress_percent: 80.0,
                progress_status: "Nearly Complete",
                monthly_required: 60000,
                remaining_amount: 300000,
                priority_recommendation: "On track"
            },
            {
                goal_id: "goal-003",
                goal_name: "Dream Vacation",
                goal_type: "SAVINGS",
                target_amount: 500000,
                current_amount: 500000,
                monthly_contribution: 0,
                expected_completion_date: "2025-01",
                months_remaining: 0,
                years_remaining: 0,
                on_track: true,
                progress_percent: 100.0,
                progress_status: "Complete",
                monthly_required: 0,
                remaining_amount: 0,
                priority_recommendation: "Completed"
            }
        ];
        
        function formatCurrency(amount) {
            return new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(amount);
        }
        
        function getStatusClass(status) {
            const classMap = {
                'Complete': 'status-complete',
                'Nearly Complete': 'status-in-progress',
                'In Progress': 'status-in-progress',
                'Just Started': 'status-just-started'
            };
            return classMap[status] || 'status-in-progress';
        }
        
        function getRecommendationClass(recommendation) {
            if (recommendation.includes('Increase contribution')) return 'urgent';
            if (recommendation === 'Completed' || recommendation === 'On track') return 'positive';
            return '';
        }
        
        function renderGoal(goal) {
            const card = document.createElement('div');
            card.className = 'goal-card';
            card.innerHTML = `
                <div class="goal-header">
                    <div>
                        <div class="goal-name">${goal.goal_name}</div>
                        <span class="goal-type">${goal.goal_type}</span>
                    </div>
                    <span class="goal-status-badge ${getStatusClass(goal.progress_status)}">
                        ${goal.progress_status}
                    </span>
                </div>
                
                <div class="goal-amounts">
                    <div class="amount-box">
                        <div class="amount-label">Target</div>
                        <div class="amount-value">${formatCurrency(goal.target_amount)}</div>
                    </div>
                    <div class="amount-box">
                        <div class="amount-label">Current</div>
                        <div class="amount-value">${formatCurrency(goal.current_amount)}</div>
                    </div>
                </div>
                
                <div class="progress-section">
                    <div class="progress-label">
                        <span class="progress-label-name">Progress</span>
                        <span class="progress-label-percent">${goal.progress_percent}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${goal.progress_percent}%"></div>
                    </div>
                </div>
                
                <div class="time-section">
                    <div class="time-box">
                        <div class="time-label">Expected Completion</div>
                        <div class="time-value">${goal.expected_completion_date || 'N/A'}</div>
                    </div>
                    <div class="time-box">
                        <div class="time-label">Time Remaining</div>
                        <div class="time-value">${goal.months_remaining} months</div>
                    </div>
                </div>
                
                ${goal.monthly_contribution > 0 ? `
                <div class="contribution-box">
                    <div class="contribution-current">
                        <div class="contribution-label">Current Monthly</div>
                        <div class="contribution-value">${formatCurrency(goal.monthly_contribution)}</div>
                    </div>
                    <div class="contribution-required">
                        <div class="contribution-label">Required</div>
                        <div class="contribution-value">${formatCurrency(goal.monthly_required)}</div>
                    </div>
                </div>
                ` : ''}
                
                <div class="recommendation-box ${getRecommendationClass(goal.priority_recommendation)}">
                    <div class="recommendation-title">Recommendation</div>
                    <div class="recommendation-text">${goal.priority_recommendation}</div>
                </div>
            `;
            return card;
        }
        
        function renderDashboard(goals) {
            const goalsGrid = document.getElementById('goalsGrid');
            goalsGrid.innerHTML = '';
            
            goals.forEach(goal => {
                goalsGrid.appendChild(renderGoal(goal));
            });
            
            // Calculate highlights
            const totalGoals = goals.length;
            const completedGoals = goals.filter(g => g.progress_percent >= 100).length;
            const onTrackGoals = goals.filter(g => g.on_track).length;
            const behindGoals = totalGoals - onTrackGoals;
            const avgProgress = (goals.reduce((sum, g) => sum + g.progress_percent, 0) / totalGoals).toFixed(1);
            
            document.getElementById('totalGoals').textContent = totalGoals;
            document.getElementById('completedGoals').textContent = completedGoals;
            document.getElementById('onTrackGoals').textContent = onTrackGoals;
            document.getElementById('behindGoals').textContent = behindGoals;
            document.getElementById('avgProgress').textContent = avgProgress + '%';
            
            // Priority section
            const highestPriority = goals.filter(g => g.progress_percent < 100).reduce((min, g) => 
                g.progress_percent < min.progress_percent ? g : min, goals[0]
            );
            const closest = goals.filter(g => g.progress_percent < 100).reduce((max, g) => 
                g.progress_percent > max.progress_percent ? g : max, goals[0]
            );
            
            if (highestPriority || closest) {
                document.getElementById('prioritySection').style.display = 'block';
                
                if (highestPriority && highestPriority.progress_percent < 100) {
                    document.getElementById('highestPriorityName').textContent = highestPriority.goal_name;
                    document.getElementById('highestPriorityProgress').textContent = 
                        `${highestPriority.progress_percent}% complete • ${formatCurrency(highestPriority.remaining_amount)} remaining`;
                }
                
                if (closest && closest.progress_percent < 100) {
                    document.getElementById('closestName').textContent = closest.goal_name;
                    document.getElementById('closestProgress').textContent = 
                        `${closest.progress_percent}% complete • Complete in ${closest.months_remaining} months`;
                }
            }
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            renderDashboard(sampleGoals);
        });
    </script>
</body>
</html>
"""

# Export for use in Flask app
def get_goals_dashboard_template():
    """Get the goals dashboard HTML template.
    
    Usage:
        from dashboard import get_goals_dashboard_template
        html = get_goals_dashboard_template()
    """
    return HTML_TEMPLATE


# Python view function example for Flask
def goals_dashboard_view():
    """Flask view function for goals dashboard.
    
    Usage in Flask app:
        from dashboard import goals_dashboard_view
        app.route('/dashboard/goals')(goals_dashboard_view)
    """
    from flask import render_template_string
    
    # In a real app, would fetch goals from database
    # and pass data to template
    return render_template_string(HTML_TEMPLATE)
