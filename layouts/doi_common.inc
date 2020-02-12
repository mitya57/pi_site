     <div id="item_name" class="item_element"><%= @item[:item_name] %></div>

     <div id="item_authors" class="item_element"><%= @item[:item_authors_address] %></div>

     <% unless @item[:item_corr_author].nil? %>
      <div id="item_corr_author" class="item_element"><i>Corresponding author:</i> <%= @item[:item_corr_author] %></div>
     <% end %>

     <% unless @item[:item_rec_on].nil? %>
      <div id="item_rec" class="item_element"><i>Received on <%= @item[:item_rec_on] %> </i></div>
     <% end %>

     <% unless @item[:item_acc_on].nil? %>
      <div id="item_acc" class="item_element"><i>Accepted on <%= @item[:item_acc_on] %> </i></div>
     <% end %>

     <div id="item_annot" class="item_element"><%= @item[:item_annot] %></div>

