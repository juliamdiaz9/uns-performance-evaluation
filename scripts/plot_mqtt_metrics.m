%% plot_mqtt_metrics.m
% =========================================================================
% MQTT Broker Performance – Metric Visualization Script
% =========================================================================
%
% Description:
%   Reads the processed Excel workbook (mqtt_metrics_processed.xlsx) and
%   generates one figure per metric sheet, overlaying the Schultz Method
%   and Parris Method time series for visual comparison.
%
%   Each plot includes:
%     - Zero-padded boundaries (curves start and end at 0)
%     - Dual-layer grid (major + minor) with soft transparency
%     - Y-axis label specific to each metric and its unit
%     - Shared horizontal legend below the X-axis
%
% Input:
%   ../data/processed/mqtt_metrics_processed.xlsx
%
% Output:
%   One MATLAB figure window per metric (24 total).
%   Figures can be saved manually or by extending the export section below.
%
% Dependencies:
%   MATLAB R2019b or later (readtable with PreserveVariableNames).
%
% Author:
%   Juliam Diaz – Master's Thesis, 2025
% =========================================================================

%% Configuration
excelFile = fullfile('..', 'data', 'processed', 'mqtt_metrics_processed.xlsx');

% Y-axis labels ordered to match the sheet sequence in the workbook
labely = {
    'Authentication [u]'
    'Authorization [u]'
    'Client Authorized [u]'
    'Client Connections [u]'
    'Connected Sessions [u]'
    'Packets Connect [u]'
    'Packets Received [u]'
    'Packets Sent [u]'
    'Packets Subscribe Received [u]'
    'PINGREQ Packets [messages/sec]'
    'Publish Messages [messages/sec]'
    'Received Bytes [Bytes/min]'
    'Received Bytes [Bytes/sec]'
    'Received Message [messages/min]'
    'Received Message [messages/sec]'
    'Received Packets [packets/min]'
    'Received Packets [packets/sec]'
    'Sent Bytes [Bytes/min]'
    'Sent Bytes [Bytes/sec]'
    'Sent Message [messages/min]'
    'Sent Message [messages/sec]'
    'Sent Packets [packets/sec]'
    'Subscriptions [u]'
    'Topics [u]'
};

%% Discover sheets
[~, sheetNames] = xlsfinfo(excelFile);

if numel(sheetNames) ~= numel(labely)
    warning('Number of sheets (%d) does not match labely entries (%d).', ...
        numel(sheetNames), numel(labely));
end

%% Main loop – one figure per metric
for i = 1:numel(sheetNames)

    sheetName = sheetNames{i};
    fprintf('Plotting sheet %2d / %2d : %s\n', i, numel(sheetNames), sheetName);

    % -----------------------------------------------------------------
    % 1. Load sheet data
    % -----------------------------------------------------------------
    T = readtable(excelFile, ...
        'Sheet', sheetName, ...
        'PreserveVariableNames', true);

    % -----------------------------------------------------------------
    % 2. Parse Time column
    % -----------------------------------------------------------------
    t = T.Time;

    if ~isdatetime(t)
        try
            % Standard format exported by the Python pipeline
            t = datetime(t, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
        catch
            % Fallback: Excel serial date number
            t = datetime(t, 'ConvertFrom', 'excel');
        end
    end

    % -----------------------------------------------------------------
    % 3. Extract metric vectors
    % -----------------------------------------------------------------
    schultz = T{:, "Schultz Method"};
    parris  = T{:, "Parris Method"};

    % Replace NaN with 0 to avoid gaps in the plot
    schultz(isnan(schultz)) = 0;
    parris(isnan(parris))   = 0;

    % -----------------------------------------------------------------
    % 4. Zero-pad boundaries
    %    Prepend and append the first/last timestamp with value = 0 so
    %    that both curves cleanly start and end at the baseline.
    % -----------------------------------------------------------------
    t_plot      = [t(1);   t;      t(end)  ];
    schultz_plot = [0;     schultz; 0       ];
    parris_plot  = [0;     parris;  0       ];

    % -----------------------------------------------------------------
    % 5. Print session statistics
    % -----------------------------------------------------------------
    fprintf('   Schultz mean = %.4f | Parris mean = %.4f\n', ...
        mean(schultz), mean(parris));

    % -----------------------------------------------------------------
    % 6. Build figure
    % -----------------------------------------------------------------
    figure('Name', sheetName, 'NumberTitle', 'off');

    % Schultz Method curve
    plot(t_plot, schultz_plot, 'LineWidth', 1.6);
    hold on;

    % Parris Method curve
    plot(t_plot, parris_plot, 'LineWidth', 1.6);

    % Grid styling
    grid on;
    grid minor;
    ax = gca;
    ax.GridAlpha      = 0.30;   % Major grid transparency
    ax.MinorGridAlpha = 0.15;   % Minor grid transparency

    % Axis labels
    xlabel('Time');
    ylabel(labely{i});

    % Y-axis upper limit: 10 % headroom above the overall maximum
    ymax = max(max(schultz_plot), max(parris_plot));
    if ymax > 0
        ylim([0, ymax * 1.1]);
    end

    % Legend below the plot area
    lgd = legend({'Schultz Method', 'Parris Method'}, ...
        'Location',    'southoutside', ...
        'Orientation', 'horizontal',   ...
        'Box',         'on');
    lgd.FontSize = 10;

    hold off;
end

fprintf('\nAll %d figures generated.\n', numel(sheetNames));
