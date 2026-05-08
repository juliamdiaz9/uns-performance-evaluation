%% plot_collected_metrics_220tags.m
% =========================================================================
% EMQX Cloud – Parris vs Schultz Method Comparison (220 tags)
% =========================================================================
%
% Description:
%   Reads the processed CSV (collected_metrics_220tags_processed.csv) and
%   generates one figure per metric, overlaying Parris Method (6 sessions)
%   and Schultz Method (3 sessions) over a common 1-hour time window
%   (60 samples, 1 min interval).
%
%   Units match the paper:
%     - Messages: messages/sec
%     - Bytes:    Bytes/sec
%
%   Colors match the paper:
%     - Blue  = Parris Method
%     - Red   = Schultz Method
%
% Input:
%   C:\Users\John Arenas\Desktop\data\uns-performance-evaluation\data\processed\collected_metrics_220tags_processed.csv
%
% Output:
%   6 figure windows (one per metric).
%
% Author:
%   Juliam Diaz – Master's Thesis, 2025
% =========================================================================

%% Path
csvFile = 'C:\Users\John Arenas\Desktop\data\uns-performance-evaluation\data\processed\collected_metrics_220tags_processed.csv';

%% Colors
C_PARRIS  = [0.85, 0.33, 0.10];   % red/orange – Parris Method
C_SCHULTZ = [0.00, 0.45, 0.74];   % blue       – Schultz Method

%% Metric definitions: {parris_col, schultz_col, y_label}
metricDefs = {
    'Parris_sessions',          'Schultz_sessions',          'Sessions [u]'
    'Parris_subscriptions',     'Schultz_subscriptions',     'Subscriptions [u]'
    'Parris_messages_inbound',  'Schultz_messages_inbound',  'Received Message [messages/sec]'
    'Parris_messages_outbound', 'Schultz_messages_outbound', 'Sent Message [messages/sec]'
    'Parris_received_bytes',    'Schultz_received_bytes',    'Received Bytes [Bytes/sec]'
    'Parris_sent_bytes',        'Schultz_sent_bytes',        'Sent Bytes [Bytes/sec]'
};

%% Load CSV
T = readtable(csvFile, 'PreserveVariableNames', true);

if ~isdatetime(T.Time)
    try
        T.Time = datetime(T.Time, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
    catch
        T.Time = datetime(T.Time, 'ConvertFrom', 'excel');
    end
end

fprintf('Loaded %d samples from: %s\n\n', height(T), csvFile);

%% Plot loop
for i = 1:size(metricDefs, 1)

    parrisCol  = metricDefs{i, 1};
    schultzCol = metricDefs{i, 2};
    ylabelStr  = metricDefs{i, 3};

    parris  = T{:, parrisCol};
    schultz = T{:, schultzCol};

    parris(isnan(parris))   = 0;
    schultz(isnan(schultz)) = 0;

    t_plot       = [T.Time(1);  T.Time;  T.Time(end)];
    parris_plot  = [0;          parris;  0           ];
    schultz_plot = [0;          schultz; 0           ];

    fprintf('Metric %d/%d: %-35s | Parris mean=%.3f | Schultz mean=%.3f\n', ...
        i, size(metricDefs,1), ylabelStr, mean(parris), mean(schultz));

    figure('Name', strrep(ylabelStr,' ','_'), 'NumberTitle', 'off');

    plot(t_plot, schultz_plot, 'Color', C_SCHULTZ, 'LineWidth', 1.6);
    hold on;
    plot(t_plot, parris_plot,  'Color', C_PARRIS,  'LineWidth', 1.6);

    grid on;
    grid minor;
    ax = gca;
    ax.GridAlpha      = 0.30;
    ax.MinorGridAlpha = 0.15;
    ax.XLim = [T.Time(1) - minutes(3), T.Time(end) + minutes(3)];
    ax.XAxis.TickLabelFormat = 'HH:mm';
    xtickformat(ax, 'HH:mm');
    xticks(ax, T.Time(1) : minutes(30) : T.Time(end));

    xlabel('Time');
    ylabel(ylabelStr);

    ymax = max(max(parris_plot), max(schultz_plot));
    if ymax > 0
        ylim([0, ymax * 1.1]);
    else
        ylim([0, 1]);
    end

    lgd = legend({'Schultz Method', 'Parris Method'}, ...
        'Location',    'southoutside', ...
        'Orientation', 'horizontal',   ...
        'Box',         'on');
    lgd.FontSize = 10;

    hold off;
end

fprintf('\nAll %d figures generated.\n', size(metricDefs,1));
