%% plot_collected_metrics_comparison.m
% =========================================================================
% EMQX Cloud – Parris vs Schultz Method Comparison (220 tags)
% =========================================================================
%
% Description:
%   Reads the processed CSV (collected_metrics_220tags_processed.csv) and
%   generates one figure per metric, overlaying Parris Method and Schultz
%   Method over a common 1-hour time window (60 samples, 1 min interval).
%   Visual style matches the original MATLAB plots (plot_mqtt_metrics.m).
%
% Input:
%   C:\Users\John Arenas\Desktop\data\uns-performance-evaluation\data\processed\collected_metrics_220tags_processed.csv
%
% Output:
%   7 figure windows (one per metric).
%
% Author:
%   Juliam Diaz – Master's Thesis, 2025
% =========================================================================

%% Path
csvFile = 'C:\Users\John Arenas\Desktop\data\uns-performance-evaluation\data\processed\collected_metrics_220tags_processed.csv';

%% Metric definitions
% Each row: {parris_col, schultz_col, y_label}
metricDefs = {
    'Parris_sessions',          'Schultz_sessions',          'Sessions [u]'
    'Parris_subscriptions',     'Schultz_subscriptions',     'Subscriptions [u]'
    'Parris_messages_inbound',  'Schultz_messages_inbound',  'Messages Inbound [messages/min]'
    'Parris_messages_outbound', 'Schultz_messages_outbound', 'Messages Outbound [messages/min]'
    'Parris_received_kb',       'Schultz_received_kb',       'Received Bytes [KB/min]'
    'Parris_sent_kb',           'Schultz_sent_kb',           'Sent Bytes [KB/min]'
    'Parris_total_kb',          'Schultz_total_kb',          'Total Bytes [KB/min]'
};

%% Load CSV
T = readtable(csvFile, 'PreserveVariableNames', true);

% Parse Time column
if ~isdatetime(T.Time)
    try
        T.Time = datetime(T.Time, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
    catch
        T.Time = datetime(T.Time, 'ConvertFrom', 'excel');
    end
end

fprintf('Loaded %d samples.\n\n', height(T));

%% Plot loop
for i = 1:size(metricDefs, 1)

    parrisCol  = metricDefs{i, 1};
    schultzCol = metricDefs{i, 2};
    ylabelStr  = metricDefs{i, 3};

    parris  = T{:, parrisCol};
    schultz = T{:, schultzCol};

    % Replace NaN with 0
    parris(isnan(parris))   = 0;
    schultz(isnan(schultz)) = 0;

    % Zero-pad boundaries
    t_plot      = [T.Time(1);  T.Time;  T.Time(end) ];
    parris_plot  = [0;          parris;  0           ];
    schultz_plot = [0;          schultz; 0           ];

    fprintf('Metric %d/%d: %-35s | Parris mean=%.2f | Schultz mean=%.2f\n', ...
        i, size(metricDefs,1), ylabelStr, mean(parris), mean(schultz));

    % --- Figure ---
    figure('Name', strrep(ylabelStr,' ','_'), 'NumberTitle', 'off');

    plot(t_plot, parris_plot,  'LineWidth', 1.6);
    hold on;
    plot(t_plot, schultz_plot, 'LineWidth', 1.6);

    % Soft grid
    grid on;
    grid minor;
    ax = gca;
    ax.GridAlpha      = 0.30;
    ax.MinorGridAlpha = 0.15;

    % Labels
    xlabel('Time');
    ylabel(ylabelStr);

    % Y-axis: 10% headroom above max of both curves
    ymax = max(max(parris_plot), max(schultz_plot));
    if ymax > 0
        ylim([0, ymax * 1.1]);
    else
        ylim([0, 1]);
    end

    % Legend below X-axis (same style as original script)
    lgd = legend({'Parris Method', 'Schultz Method'}, ...
        'Location',    'southoutside', ...
        'Orientation', 'horizontal',   ...
        'Box',         'on');
    lgd.FontSize = 10;

    hold off;
end

fprintf('\nAll %d figures generated.\n', size(metricDefs,1));
